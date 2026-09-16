#!/usr/bin/env python3
"""
llm_screening.py

Screen NOW corpus news articles with a GPT model and classify them into
CORE / PERIPHERAL / EXCLUDE for downstream discourse analysis.

The programme is manifest-driven: it reads an immutable NDJSON manifest whose
rows contain at least an article_id and filepath. For each article, it reads
the article text, inserts it into an external Markdown prompt template, calls
the OpenAI Responses API, validates the JSON response, writes a per-article
JSON artefact, and builds consolidated run-level outputs.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import logging
import os
import re
import sys
import tempfile
import threading
import time
import traceback
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


PROGRAMME_NAME = "llm_screening.py"
ARTICLE_TEXT_PLACEHOLDER = "<<<ARTICLE_TEXT>>>"

ALLOWED_CATEGORIES = {"CORE", "PERIPHERAL", "EXCLUDE"}
ALLOWED_GAZA_ROLES = {
    "central",
    "substantial",
    "background",
    "passing",
    "boilerplate_or_unrelated",
}

TEMPERATURE_UNSUPPORTED_MODELS: set[str] = set()
TEMPERATURE_SUPPORT_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# Generic utilities
# ---------------------------------------------------------------------------


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_path(path_value: str | Path, base_dir: Path) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def relpath(path: Path, base_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(base_dir.resolve()))
    except ValueError:
        return str(path.resolve())


def safe_path_part(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    if not text:
        return fallback
    text = text.replace("\\", "_").replace("/", "_")
    text = re.sub(r"[^A-Za-z0-9._=-]+", "_", text)
    return text or fallback


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_file(path: Path, data: Dict[str, Any]) -> None:
    write_text_atomic(path, json.dumps(data, ensure_ascii=False, indent=2))


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)
        handle.write(text)
        handle.write("\n")
    temp_path.replace(path)


def write_ndjson_file(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")
    temp_path.replace(path)


def load_dotenv_file(path: Path) -> bool:
    """
    Minimal .env loader.

    Supports simple KEY=VALUE lines. Existing environment variables are not
    overwritten.
    """
    if not path.exists():
        return False

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if (
            (value.startswith('"') and value.endswith('"'))
            or (value.startswith("'") and value.endswith("'"))
        ):
            value = value[1:-1]

        os.environ.setdefault(key, value)

    return True


def extract_response_text(response: Any) -> str:
    """
    Extract text from an OpenAI Responses API result robustly.
    """
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = getattr(response, "output", None)
    parts: List[str] = []
    if output:
        for item in output:
            content = getattr(item, "content", None)
            if not content:
                continue
            for content_item in content:
                text = getattr(content_item, "text", None)
                if text:
                    parts.append(str(text))

    return "\n".join(parts).strip()


def api_metadata_from_response(response: Any) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {}

    for attr in ("id", "model", "created_at", "status"):
        value = getattr(response, attr, None)
        if value is not None:
            metadata[attr] = value

    usage = getattr(response, "usage", None)
    if usage is not None:
        try:
            if hasattr(usage, "model_dump"):
                metadata["usage"] = usage.model_dump()
            elif hasattr(usage, "dict"):
                metadata["usage"] = usage.dict()
            else:
                metadata["usage"] = str(usage)
        except Exception:
            metadata["usage"] = str(usage)

    return metadata


def usage_totals_from_results(results: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }

    input_keys = ("input_tokens", "prompt_tokens")
    output_keys = ("output_tokens", "completion_tokens")
    total_keys = ("total_tokens",)

    for result in results:
        usage = result.get("api_metadata", {}).get("usage")
        if not isinstance(usage, dict):
            continue

        for key in input_keys:
            value = usage.get(key)
            if isinstance(value, int):
                totals["input_tokens"] += value
                break

        for key in output_keys:
            value = usage.get(key)
            if isinstance(value, int):
                totals["output_tokens"] += value
                break

        for key in total_keys:
            value = usage.get(key)
            if isinstance(value, int):
                totals["total_tokens"] += value
                break

    if totals["total_tokens"] == 0:
        totals["total_tokens"] = totals["input_tokens"] + totals["output_tokens"]

    return totals


# ---------------------------------------------------------------------------
# Argument parsing and configuration
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Screen NOW corpus news articles with a GPT model."
    )

    parser.add_argument("--manifest", required=True, help="Input NDJSON article manifest.")
    parser.add_argument("--output", required=True, help="Output directory for screening results.")
    parser.add_argument("--prompt", required=True, help="Markdown screening prompt template.")
    parser.add_argument("--model", required=True, help="GPT model ID used for screening.")

    parser.add_argument("--limit", type=int, default=None, help="Process only first N planned articles.")
    parser.add_argument("--resume", action="store_true", help="Skip existing successful per-article outputs.")
    parser.add_argument("--reprocess", action="store_true", help="Reprocess even if successful outputs exist.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and plan without API calls.")

    parser.add_argument("--workers", type=int, default=1, help="Number of concurrent workers.")
    parser.add_argument("--max-retries", type=int, default=2, help="API retries after initial attempt.")
    parser.add_argument("--retry-backoff-seconds", type=float, default=5.0, help="Initial retry backoff.")
    parser.add_argument("--temperature", type=float, default=0.0, help="Temperature if supported.")
    parser.add_argument("--max-output-tokens", type=int, default=500, help="Max output tokens if supported.")

    parser.add_argument("--env-file", default="env/.env", help="Optional .env file.")
    parser.add_argument("--log-file", default=None, help="Optional explicit log file.")
    parser.add_argument("--manifest-file", default=None, help="Optional explicit latest run manifest file.")

    parser.add_argument("--article-id-field", default="article_id")
    parser.add_argument("--filepath-field", default="filepath")
    parser.add_argument("--group-field", default="group")
    parser.add_argument("--country-code-field", default="country_code")

    return parser


@dataclass
class Config:
    script_dir: Path
    run_id: str

    manifest: Path
    output: Path
    prompt: Path
    model: str

    limit: Optional[int]
    resume: bool
    reprocess: bool
    dry_run: bool

    workers: int
    max_retries: int
    retry_backoff_seconds: float
    temperature: float
    max_output_tokens: int

    env_file: Path
    log_file: Path
    manifest_file: Path
    timestamped_manifest_file: Path

    article_id_field: str
    filepath_field: str
    group_field: str
    country_code_field: str

    screening_json_dir: Path
    screened_ndjson: Path
    failures_ndjson: Path
    invalid_responses_ndjson: Path
    summary_file: Path


def make_config(args: argparse.Namespace) -> Config:
    script_dir = Path(__file__).resolve().parent
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]

    output = resolve_path(args.output, script_dir)
    log_file = resolve_path(args.log_file, script_dir) if args.log_file else output / "llm_screening.log"
    manifest_file = (
        resolve_path(args.manifest_file, script_dir)
        if args.manifest_file
        else output / "llm_screening_manifest.json"
    )

    return Config(
        script_dir=script_dir,
        run_id=run_id,
        manifest=resolve_path(args.manifest, script_dir),
        output=output,
        prompt=resolve_path(args.prompt, script_dir),
        model=args.model,
        limit=args.limit,
        resume=args.resume,
        reprocess=args.reprocess,
        dry_run=args.dry_run,
        workers=args.workers,
        max_retries=args.max_retries,
        retry_backoff_seconds=args.retry_backoff_seconds,
        temperature=args.temperature,
        max_output_tokens=args.max_output_tokens,
        env_file=resolve_path(args.env_file, script_dir),
        log_file=log_file,
        manifest_file=manifest_file,
        timestamped_manifest_file=output / f"llm_screening_manifest_{run_id}.json",
        article_id_field=args.article_id_field,
        filepath_field=args.filepath_field,
        group_field=args.group_field,
        country_code_field=args.country_code_field,
        screening_json_dir=output / "screening_json",
        screened_ndjson=output / "palestine_now_screened.ndjson",
        failures_ndjson=output / "llm_screening_failures.ndjson",
        invalid_responses_ndjson=output / "llm_screening_invalid_responses.ndjson",
        summary_file=output / "llm_screening_summary.json",
    )


# ---------------------------------------------------------------------------
# Logging and validation
# ---------------------------------------------------------------------------


def setup_logging(config: Config) -> None:
    config.log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(config.log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )


def validate_basic_options(config: Config) -> None:
    if not config.model.strip():
        raise ValueError("--model must not be empty")
    if config.limit is not None and config.limit <= 0:
        raise ValueError("--limit must be greater than 0 when supplied")
    if config.workers <= 0:
        raise ValueError("--workers must be greater than 0")
    if config.max_retries < 0:
        raise ValueError("--max-retries must be greater than or equal to 0")
    if config.retry_backoff_seconds < 0:
        raise ValueError("--retry-backoff-seconds must be greater than or equal to 0")
    if config.temperature < 0:
        raise ValueError("--temperature must be greater than or equal to 0")
    if config.max_output_tokens <= 0:
        raise ValueError("--max-output-tokens must be greater than 0")


def validate_paths(config: Config) -> None:
    if not config.manifest.exists() or not config.manifest.is_file():
        raise FileNotFoundError(f"Manifest file not found: {relpath(config.manifest, config.script_dir)}")
    if not config.prompt.exists() or not config.prompt.is_file():
        raise FileNotFoundError(f"Prompt file not found: {relpath(config.prompt, config.script_dir)}")

    config.output.mkdir(parents=True, exist_ok=True)
    config.screening_json_dir.mkdir(parents=True, exist_ok=True)


def load_prompt(config: Config) -> str:
    prompt = read_text_file(config.prompt)
    if not prompt.strip():
        raise ValueError(f"Prompt template is empty: {relpath(config.prompt, config.script_dir)}")
    if ARTICLE_TEXT_PLACEHOLDER not in prompt:
        raise ValueError(f"Prompt template must contain {ARTICLE_TEXT_PLACEHOLDER}")
    return prompt.strip()


# ---------------------------------------------------------------------------
# Manifest handling
# ---------------------------------------------------------------------------


def load_manifest_rows(config: Config) -> Tuple[List[Dict[str, Any]], str]:
    rows: List[Dict[str, Any]] = []

    with config.manifest.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in manifest at line {line_number}: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"Manifest line {line_number} is not a JSON object")
            rows.append({"line_number": line_number, "row": item})

    if not rows:
        raise ValueError(f"Manifest is empty: {relpath(config.manifest, config.script_dir)}")

    return rows, sha256_file(config.manifest)


def get_article_id(config: Config, manifest_row: Dict[str, Any], fallback: str) -> str:
    value = manifest_row.get(config.article_id_field)
    if value is None or str(value).strip() == "":
        return fallback
    return str(value).strip()


def expected_article_output_path(config: Config, manifest_row: Dict[str, Any], article_id: str) -> Path:
    group = safe_path_part(manifest_row.get(config.group_field), "unknown_group")
    country = safe_path_part(manifest_row.get(config.country_code_field), "unknown_country")
    article = safe_path_part(article_id, "unknown_article")
    return config.screening_json_dir / group / country / f"{article}.json"


def existing_success(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return isinstance(data, dict) and data.get("status") == "success"


def read_existing_result(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data["status"] = "skipped_existing"
            data["skipped_at"] = utc_now_iso()
            return data
    except Exception:
        pass
    return {
        "status": "failed",
        "error_type": "invalid_existing_output",
        "error": f"Could not read existing output: {path}",
    }


def validate_manifest_row(config: Config, manifest_row: Dict[str, Any]) -> Optional[str]:
    if config.article_id_field not in manifest_row or str(manifest_row.get(config.article_id_field, "")).strip() == "":
        return f"Missing required manifest field: {config.article_id_field}"
    if config.filepath_field not in manifest_row or str(manifest_row.get(config.filepath_field, "")).strip() == "":
        return f"Missing required manifest field: {config.filepath_field}"
    return None


# ---------------------------------------------------------------------------
# OpenAI API
# ---------------------------------------------------------------------------


def import_openai_client_class() -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError("The OpenAI Python SDK is unavailable. Install it with: pip install openai") from exc
    return OpenAI


def make_openai_client() -> Any:
    OpenAI = import_openai_client_class()
    return OpenAI()


def call_openai_with_retries(
    client: Any,
    *,
    model: str,
    prompt: str,
    temperature: float,
    max_output_tokens: int,
    max_retries: int,
    retry_backoff_seconds: float,
) -> Tuple[str, Dict[str, Any], bool, bool]:
    """
    Returns:
        response_text, api_metadata, temperature_sent, max_output_tokens_sent
    """
    last_error: Optional[BaseException] = None

    for attempt in range(max_retries + 1):
        try:
            kwargs: Dict[str, Any] = {
                "model": model,
                "input": prompt,
            }

            temperature_sent = False
            max_output_tokens_sent = False

            with TEMPERATURE_SUPPORT_LOCK:
                model_supports_temperature = model not in TEMPERATURE_UNSUPPORTED_MODELS

            if temperature is not None and model_supports_temperature:
                kwargs["temperature"] = temperature
                temperature_sent = True

            if max_output_tokens is not None:
                kwargs["max_output_tokens"] = max_output_tokens
                max_output_tokens_sent = True

            try:
                response = client.responses.create(**kwargs)
            except TypeError as exc:
                # Conservative fallback for SDK/client signature mismatch.
                if "temperature" in kwargs:
                    kwargs.pop("temperature", None)
                    temperature_sent = False
                    with TEMPERATURE_SUPPORT_LOCK:
                        TEMPERATURE_UNSUPPORTED_MODELS.add(model)
                    response = client.responses.create(**kwargs)
                else:
                    raise exc
            except Exception as exc:
                error_text = str(exc)

                if (
                    "Unsupported parameter" in error_text
                    and "temperature" in error_text
                    and "temperature" in kwargs
                ):
                    logging.warning(
                        "Model %s does not support temperature; omitting temperature for subsequent requests.",
                        model,
                    )
                    kwargs.pop("temperature", None)
                    temperature_sent = False
                    with TEMPERATURE_SUPPORT_LOCK:
                        TEMPERATURE_UNSUPPORTED_MODELS.add(model)
                    response = client.responses.create(**kwargs)

                elif (
                    "Unsupported parameter" in error_text
                    and "max_output_tokens" in error_text
                    and "max_output_tokens" in kwargs
                ):
                    logging.warning(
                        "Model/API rejected max_output_tokens; retrying current request without it."
                    )
                    kwargs.pop("max_output_tokens", None)
                    max_output_tokens_sent = False
                    response = client.responses.create(**kwargs)

                else:
                    raise

            text = extract_response_text(response)
            metadata = api_metadata_from_response(response)

            if not text.strip():
                raise ValueError("LLM response contains no usable text")

            return text.strip(), metadata, temperature_sent, max_output_tokens_sent

        except Exception as exc:
            last_error = exc
            if attempt >= max_retries:
                break
            sleep_for = retry_backoff_seconds * (2 ** attempt)
            logging.warning("API call failed on attempt %s/%s: %s", attempt + 1, max_retries + 1, exc)
            if sleep_for > 0:
                time.sleep(sleep_for)

    raise RuntimeError(f"LLM request failed after {max_retries + 1} attempt(s): {last_error}") from last_error


# ---------------------------------------------------------------------------
# Response parsing and validation
# ---------------------------------------------------------------------------


def parse_llm_json_response(raw_response_text: str) -> Dict[str, Any]:
    text = raw_response_text.strip()

    # Be tolerant of accidental fenced JSON responses.
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response JSON is not an object")
    return parsed


def validate_screening_response(screening: Dict[str, Any]) -> None:
    required_fields = {
        "category",
        "confidence",
        "gaza_role",
        "main_topic",
        "conflict_relevance",
        "reason",
        "multi_article_or_snippet_issue",
        "recommended_for_main_corpus",
    }

    missing = sorted(required_fields - set(screening.keys()))
    if missing:
        raise ValueError(f"LLM response missing required fields: {', '.join(missing)}")

    category = screening.get("category")
    if category not in ALLOWED_CATEGORIES:
        raise ValueError(f"Invalid category: {category}")

    confidence = screening.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise ValueError("confidence must be numeric")
    if confidence < 0.0 or confidence > 1.0:
        raise ValueError("confidence must be between 0.0 and 1.0")

    gaza_role = screening.get("gaza_role")
    if gaza_role not in ALLOWED_GAZA_ROLES:
        raise ValueError(f"Invalid gaza_role: {gaza_role}")

    for field in ("main_topic", "conflict_relevance", "reason"):
        if not isinstance(screening.get(field), str):
            raise ValueError(f"{field} must be a string")

    if not isinstance(screening.get("multi_article_or_snippet_issue"), bool):
        raise ValueError("multi_article_or_snippet_issue must be boolean")

    recommended = screening.get("recommended_for_main_corpus")
    if not isinstance(recommended, bool):
        raise ValueError("recommended_for_main_corpus must be boolean")

    if recommended and category != "CORE":
        raise ValueError("recommended_for_main_corpus can be true only when category == CORE")


# ---------------------------------------------------------------------------
# Record builders
# ---------------------------------------------------------------------------


def build_screening_prompt(prompt_template: str, article_text: str) -> str:
    return prompt_template.replace(ARTICLE_TEXT_PLACEHOLDER, article_text)


def build_base_input_block(config: Config, manifest_row: Dict[str, Any], article_file: Optional[Path]) -> Dict[str, Any]:
    return {
        "manifest_file": relpath(config.manifest, config.script_dir),
        "article_file": relpath(article_file, config.script_dir) if article_file is not None else None,
        "prompt_file": relpath(config.prompt, config.script_dir),
    }


def build_failure_record(
    *,
    config: Config,
    manifest_row: Dict[str, Any],
    article_id: str,
    article_file: Optional[Path],
    output_path: Path,
    error_type: str,
    error: str,
    duration_seconds: float = 0.0,
) -> Dict[str, Any]:
    return {
        "article_id": article_id,
        "status": "failed",
        "input": build_base_input_block(config, manifest_row, article_file),
        "output": {
            "per_article_json": relpath(output_path, config.script_dir),
        },
        "manifest_row": manifest_row,
        "error_type": error_type,
        "error": error,
        "created_at": utc_now_iso(),
        "duration_seconds": round(duration_seconds, 3),
    }


def build_invalid_response_record(
    *,
    config: Config,
    manifest_row: Dict[str, Any],
    article_id: str,
    article_file: Path,
    output_path: Path,
    raw_response_text: str,
    api_metadata: Dict[str, Any],
    validation_error: str,
    temperature_sent: bool,
    max_output_tokens_sent: bool,
    hashes: Dict[str, Any],
    duration_seconds: float,
) -> Dict[str, Any]:
    return {
        "article_id": article_id,
        "status": "invalid_response",
        "input": build_base_input_block(config, manifest_row, article_file),
        "output": {
            "per_article_json": relpath(output_path, config.script_dir),
        },
        "manifest_row": manifest_row,
        "raw_response_text": raw_response_text,
        "validation_error": validation_error,
        "api_metadata": api_metadata,
        "hashes": hashes,
        "model": {
            "configured_model": config.model,
            "response_model": api_metadata.get("model", config.model),
        },
        "temperature": config.temperature,
        "temperature_sent_to_api": temperature_sent,
        "max_output_tokens": config.max_output_tokens,
        "max_output_tokens_sent_to_api": max_output_tokens_sent,
        "created_at": utc_now_iso(),
        "duration_seconds": round(duration_seconds, 3),
    }


def build_success_record(
    *,
    config: Config,
    manifest_row: Dict[str, Any],
    article_id: str,
    article_file: Path,
    output_path: Path,
    screening: Dict[str, Any],
    raw_response_text: str,
    api_metadata: Dict[str, Any],
    temperature_sent: bool,
    max_output_tokens_sent: bool,
    hashes: Dict[str, Any],
    duration_seconds: float,
) -> Dict[str, Any]:
    return {
        "article_id": article_id,
        "status": "success",
        "input": build_base_input_block(config, manifest_row, article_file),
        "output": {
            "per_article_json": relpath(output_path, config.script_dir),
        },
        "manifest_row": manifest_row,
        "screening": screening,
        "model": {
            "configured_model": config.model,
            "response_model": api_metadata.get("model", config.model),
        },
        "hashes": hashes,
        "api_metadata": api_metadata,
        "raw_response_text": raw_response_text,
        "temperature": config.temperature,
        "temperature_sent_to_api": temperature_sent,
        "max_output_tokens": config.max_output_tokens,
        "max_output_tokens_sent_to_api": max_output_tokens_sent,
        "created_at": utc_now_iso(),
        "duration_seconds": round(duration_seconds, 3),
        "error": None,
    }


# ---------------------------------------------------------------------------
# Per-article processing
# ---------------------------------------------------------------------------


def process_one_article(
    planned_item: Dict[str, Any],
    *,
    config: Config,
    client: Any,
    prompt_template: str,
    manifest_sha256: str,
    prompt_sha256: str,
) -> Dict[str, Any]:
    start_time = time.time()
    manifest_row = planned_item["manifest_row"]
    article_id = planned_item["article_id"]
    output_path = planned_item["output_path"]

    article_file: Optional[Path] = None

    try:
        row_error = validate_manifest_row(config, manifest_row)
        if row_error:
            record = build_failure_record(
                config=config,
                manifest_row=manifest_row,
                article_id=article_id,
                article_file=None,
                output_path=output_path,
                error_type="invalid_manifest_row",
                error=row_error,
                duration_seconds=time.time() - start_time,
            )
            write_json_file(output_path, record)
            return record

        article_file = resolve_path(str(manifest_row[config.filepath_field]), config.script_dir)

        if not article_file.exists() or not article_file.is_file():
            record = build_failure_record(
                config=config,
                manifest_row=manifest_row,
                article_id=article_id,
                article_file=article_file,
                output_path=output_path,
                error_type="missing_article_file",
                error="Article file not found",
                duration_seconds=time.time() - start_time,
            )
            write_json_file(output_path, record)
            return record

        article_text = read_text_file(article_file)
        if not article_text.strip():
            record = build_failure_record(
                config=config,
                manifest_row=manifest_row,
                article_id=article_id,
                article_file=article_file,
                output_path=output_path,
                error_type="empty_article_file",
                error="Article file is empty",
                duration_seconds=time.time() - start_time,
            )
            write_json_file(output_path, record)
            return record

        rendered_prompt = build_screening_prompt(prompt_template, article_text)

        hashes = {
            "manifest_file_sha256": manifest_sha256,
            "article_text_sha256": sha256_text(article_text),
            "prompt_template_sha256": prompt_sha256,
            "rendered_prompt_sha256": sha256_text(rendered_prompt),
        }

        raw_response_text, api_metadata, temperature_sent, max_output_tokens_sent = call_openai_with_retries(
            client,
            model=config.model,
            prompt=rendered_prompt,
            temperature=config.temperature,
            max_output_tokens=config.max_output_tokens,
            max_retries=config.max_retries,
            retry_backoff_seconds=config.retry_backoff_seconds,
        )

        hashes["raw_response_text_sha256"] = sha256_text(raw_response_text)

        try:
            screening = parse_llm_json_response(raw_response_text)
            validate_screening_response(screening)
        except Exception as exc:
            record = build_invalid_response_record(
                config=config,
                manifest_row=manifest_row,
                article_id=article_id,
                article_file=article_file,
                output_path=output_path,
                raw_response_text=raw_response_text,
                api_metadata=api_metadata,
                validation_error=str(exc),
                temperature_sent=temperature_sent,
                max_output_tokens_sent=max_output_tokens_sent,
                hashes=hashes,
                duration_seconds=time.time() - start_time,
            )
            write_json_file(output_path, record)
            return record

        record = build_success_record(
            config=config,
            manifest_row=manifest_row,
            article_id=article_id,
            article_file=article_file,
            output_path=output_path,
            screening=screening,
            raw_response_text=raw_response_text,
            api_metadata=api_metadata,
            temperature_sent=temperature_sent,
            max_output_tokens_sent=max_output_tokens_sent,
            hashes=hashes,
            duration_seconds=time.time() - start_time,
        )
        write_json_file(output_path, record)
        return record

    except Exception as exc:
        logging.error("Failed article %s: %s", article_id, exc)
        logging.debug("Traceback for article %s:\n%s", article_id, traceback.format_exc())

        record = build_failure_record(
            config=config,
            manifest_row=manifest_row,
            article_id=article_id,
            article_file=article_file,
            output_path=output_path,
            error_type="processing_error",
            error=str(exc),
            duration_seconds=time.time() - start_time,
        )

        try:
            write_json_file(output_path, record)
        except Exception as write_exc:
            logging.error("Could not write failure JSON for article %s: %s", article_id, write_exc)

        return record


def build_dry_run_record(
    planned_item: Dict[str, Any],
    *,
    config: Config,
    prompt_template: str,
    manifest_sha256: str,
    prompt_sha256: str,
) -> Dict[str, Any]:
    start_time = time.time()
    manifest_row = planned_item["manifest_row"]
    article_id = planned_item["article_id"]
    output_path = planned_item["output_path"]
    article_file: Optional[Path] = None

    try:
        row_error = validate_manifest_row(config, manifest_row)
        if row_error:
            return build_failure_record(
                config=config,
                manifest_row=manifest_row,
                article_id=article_id,
                article_file=None,
                output_path=output_path,
                error_type="invalid_manifest_row",
                error=row_error,
                duration_seconds=time.time() - start_time,
            )

        article_file = resolve_path(str(manifest_row[config.filepath_field]), config.script_dir)

        exists = article_file.exists() and article_file.is_file()
        article_text_sha256 = None
        rendered_prompt_sha256 = None
        article_chars = 0
        rendered_prompt_chars = 0

        if exists:
            article_text = read_text_file(article_file)
            article_chars = len(article_text)
            article_text_sha256 = sha256_text(article_text)
            rendered_prompt = build_screening_prompt(prompt_template, article_text)
            rendered_prompt_chars = len(rendered_prompt)
            rendered_prompt_sha256 = sha256_text(rendered_prompt)

        return {
            "article_id": article_id,
            "status": "dry_run",
            "input": build_base_input_block(config, manifest_row, article_file),
            "output": {
                "per_article_json": relpath(output_path, config.script_dir),
            },
            "manifest_row": manifest_row,
            "checks": {
                "article_file_exists": exists,
                "article_chars": article_chars,
                "rendered_prompt_chars": rendered_prompt_chars,
            },
            "hashes": {
                "manifest_file_sha256": manifest_sha256,
                "prompt_template_sha256": prompt_sha256,
                "article_text_sha256": article_text_sha256,
                "rendered_prompt_sha256": rendered_prompt_sha256,
            },
            "created_at": utc_now_iso(),
            "duration_seconds": round(time.time() - start_time, 3),
        }

    except Exception as exc:
        return build_failure_record(
            config=config,
            manifest_row=manifest_row,
            article_id=article_id,
            article_file=article_file,
            output_path=output_path,
            error_type="dry_run_error",
            error=str(exc),
            duration_seconds=time.time() - start_time,
        )


# ---------------------------------------------------------------------------
# Output aggregation
# ---------------------------------------------------------------------------


def count_statuses(results: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counts = {
        "articles_succeeded": 0,
        "articles_failed": 0,
        "articles_invalid_response": 0,
        "articles_skipped_existing": 0,
        "articles_dry_run": 0,
        "category_core": 0,
        "category_peripheral": 0,
        "category_exclude": 0,
    }

    for result in results:
        status = result.get("status")
        if status == "success":
            counts["articles_succeeded"] += 1
        elif status == "failed":
            counts["articles_failed"] += 1
        elif status == "invalid_response":
            counts["articles_invalid_response"] += 1
        elif status == "skipped_existing":
            counts["articles_skipped_existing"] += 1
        elif status == "dry_run":
            counts["articles_dry_run"] += 1

        screening = result.get("screening")
        if isinstance(screening, dict):
            category = screening.get("category")
            if category == "CORE":
                counts["category_core"] += 1
            elif category == "PERIPHERAL":
                counts["category_peripheral"] += 1
            elif category == "EXCLUDE":
                counts["category_exclude"] += 1

    return counts


def build_consolidated_success_row(config: Config, result: Dict[str, Any]) -> Dict[str, Any]:
    row = dict(result.get("manifest_row", {}))
    row["llm_screening"] = result.get("screening", {})
    row["llm_screening_metadata"] = {
        "status": result.get("status"),
        "model": result.get("model", {}).get("configured_model", config.model),
        "response_model": result.get("model", {}).get("response_model"),
        "prompt_file": relpath(config.prompt, config.script_dir),
        "prompt_template_sha256": result.get("hashes", {}).get("prompt_template_sha256"),
        "screened_at": result.get("created_at"),
        "per_article_json": result.get("output", {}).get("per_article_json"),
        "temperature": result.get("temperature"),
        "temperature_sent_to_api": result.get("temperature_sent_to_api"),
        "max_output_tokens": result.get("max_output_tokens"),
        "max_output_tokens_sent_to_api": result.get("max_output_tokens_sent_to_api"),
        "usage": result.get("api_metadata", {}).get("usage", {}),
    }
    return row


def write_run_outputs(
    *,
    config: Config,
    manifest_rows_total: int,
    planned_items: List[Dict[str, Any]],
    results: List[Dict[str, Any]],
    manifest_sha256: str,
    prompt_sha256: str,
    environment_metadata: Dict[str, Any],
    run_start: str,
    run_end: str,
) -> Dict[str, Any]:
    result_by_article_id = {
        str(result.get("article_id")): result
        for result in results
        if result.get("article_id") is not None
    }

    ordered_results: List[Dict[str, Any]] = []
    for item in planned_items:
        result = result_by_article_id.get(str(item["article_id"]))
        if result is not None:
            ordered_results.append(result)

    successes = [
        build_consolidated_success_row(config, result)
        for result in ordered_results
        if result.get("status") in {"success", "skipped_existing"} and isinstance(result.get("screening"), dict)
    ]

    failures = [result for result in ordered_results if result.get("status") == "failed"]
    invalid_responses = [result for result in ordered_results if result.get("status") == "invalid_response"]

    write_ndjson_file(config.screened_ndjson, successes)
    write_ndjson_file(config.failures_ndjson, failures)
    write_ndjson_file(config.invalid_responses_ndjson, invalid_responses)

    counts = count_statuses(ordered_results)
    usage_totals = usage_totals_from_results(ordered_results)

    summary = {
        "run_id": config.run_id,
        "programme": PROGRAMME_NAME,
        "model": config.model,
        "prompt": relpath(config.prompt, config.script_dir),
        "manifest": relpath(config.manifest, config.script_dir),
        "screened_ndjson": relpath(config.screened_ndjson, config.script_dir),
        "counts": {
            "manifest_rows_total": manifest_rows_total,
            "articles_planned": len(planned_items),
            **counts,
        },
        "usage_totals": usage_totals,
    }

    write_json_file(config.summary_file, summary)

    with TEMPERATURE_SUPPORT_LOCK:
        temperature_unsupported_models = sorted(TEMPERATURE_UNSUPPORTED_MODELS)

    run_manifest = {
        "run_id": config.run_id,
        "programme": PROGRAMME_NAME,
        "start_time": run_start,
        "end_time": run_end,
        "status": "success" if counts["articles_failed"] == 0 and counts["articles_invalid_response"] == 0 else "completed_with_errors",
        "paths": {
            "manifest": relpath(config.manifest, config.script_dir),
            "output": relpath(config.output, config.script_dir),
            "prompt": relpath(config.prompt, config.script_dir),
            "log_file": relpath(config.log_file, config.script_dir),
            "screening_json_dir": relpath(config.screening_json_dir, config.script_dir),
            "screened_ndjson": relpath(config.screened_ndjson, config.script_dir),
            "failures_ndjson": relpath(config.failures_ndjson, config.script_dir),
            "invalid_responses_ndjson": relpath(config.invalid_responses_ndjson, config.script_dir),
            "summary_file": relpath(config.summary_file, config.script_dir),
            "manifest_file": relpath(config.manifest_file, config.script_dir),
            "timestamped_manifest_file": relpath(config.timestamped_manifest_file, config.script_dir),
        },
        "environment": environment_metadata,
        "model_configuration": {
            "model": config.model,
            "temperature": config.temperature,
            "max_output_tokens": config.max_output_tokens,
            "temperature_unsupported_models": temperature_unsupported_models,
        },
        "processing": {
            "workers": config.workers,
            "limit": config.limit,
            "resume": config.resume,
            "reprocess": config.reprocess,
            "dry_run": config.dry_run,
            "max_retries": config.max_retries,
            "retry_backoff_seconds": config.retry_backoff_seconds,
            "order": "manifest_order",
        },
        "hashes": {
            "manifest_file_sha256": manifest_sha256,
            "prompt_template_sha256": prompt_sha256,
        },
        "counts": {
            "manifest_rows_total": manifest_rows_total,
            "articles_planned": len(planned_items),
            **counts,
        },
        "usage_totals": usage_totals,
        "articles": [
            {
                "article_id": result.get("article_id"),
                "status": result.get("status"),
                "category": result.get("screening", {}).get("category")
                if isinstance(result.get("screening"), dict)
                else None,
                "per_article_json": result.get("output", {}).get("per_article_json"),
                "error": result.get("error") or result.get("validation_error"),
            }
            for result in ordered_results
        ],
    }

    write_json_file(config.manifest_file, run_manifest)
    write_json_file(config.timestamped_manifest_file, run_manifest)

    return run_manifest


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    args = build_arg_parser().parse_args()
    config = make_config(args)
    run_start = utc_now_iso()

    try:
        config.output.mkdir(parents=True, exist_ok=True)
        setup_logging(config)

        logging.info("Starting %s run_id=%s", PROGRAMME_NAME, config.run_id)

        validate_basic_options(config)
        validate_paths(config)

        env_file_found = load_dotenv_file(config.env_file)
        api_key_available = bool(os.environ.get("OPENAI_API_KEY"))

        environment_metadata = {
            "env_file": relpath(config.env_file, config.script_dir),
            "env_file_found": env_file_found,
            "openai_api_key_available": api_key_available,
            "openai_api_key_source": "env_file_or_process_environment" if api_key_available else None,
            "openai_api_key_logged": False,
        }

        if not config.dry_run and not api_key_available:
            raise RuntimeError(
                f"OPENAI_API_KEY is not available after checking "
                f"{relpath(config.env_file, config.script_dir)} and the process environment"
            )

        prompt_template = load_prompt(config)
        prompt_sha256 = sha256_text(prompt_template)

        manifest_entries, manifest_sha256 = load_manifest_rows(config)
        manifest_rows_total = len(manifest_entries)

        planned_items: List[Dict[str, Any]] = []
        for entry in manifest_entries:
            row = entry["row"]
            article_id = get_article_id(config, row, fallback=f"manifest_line_{entry['line_number']}")
            output_path = expected_article_output_path(config, row, article_id)
            planned_items.append(
                {
                    "line_number": entry["line_number"],
                    "manifest_row": row,
                    "article_id": article_id,
                    "output_path": output_path,
                }
            )

        if config.limit is not None:
            planned_items = planned_items[: config.limit]

        logging.info("Manifest rows: %s; planned articles: %s", manifest_rows_total, len(planned_items))
        logging.info("Model: %s", config.model)
        logging.info("Prompt SHA-256: %s", prompt_sha256)
        logging.info("Manifest SHA-256: %s", manifest_sha256)

        if config.reprocess and config.resume:
            logging.warning("--reprocess supplied with --resume; reprocess takes precedence.")

        results: List[Dict[str, Any]] = []

        items_to_process: List[Dict[str, Any]] = []
        for item in planned_items:
            output_path = item["output_path"]

            if config.resume and not config.reprocess and existing_success(output_path):
                result = read_existing_result(output_path)
                results.append(result)
                logging.info("Skipping existing successful article: %s", item["article_id"])
            else:
                items_to_process.append(item)

        logging.info("Articles to process: %s; skipped existing: %s", len(items_to_process), len(results))

        if config.dry_run:
            for item in items_to_process:
                result = build_dry_run_record(
                    item,
                    config=config,
                    prompt_template=prompt_template,
                    manifest_sha256=manifest_sha256,
                    prompt_sha256=prompt_sha256,
                )
                results.append(result)

            run_end = utc_now_iso()
            run_manifest = write_run_outputs(
                config=config,
                manifest_rows_total=manifest_rows_total,
                planned_items=planned_items,
                results=results,
                manifest_sha256=manifest_sha256,
                prompt_sha256=prompt_sha256,
                environment_metadata=environment_metadata,
                run_start=run_start,
                run_end=run_end,
            )
            logging.info("Dry run completed: %s", run_manifest["counts"])
            return 0

        client = make_openai_client()

        if config.workers == 1:
            for item in items_to_process:
                logging.info("Processing article: %s", item["article_id"])
                result = process_one_article(
                    item,
                    config=config,
                    client=client,
                    prompt_template=prompt_template,
                    manifest_sha256=manifest_sha256,
                    prompt_sha256=prompt_sha256,
                )
                results.append(result)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=config.workers) as executor:
                future_to_item = {
                    executor.submit(
                        process_one_article,
                        item,
                        config=config,
                        client=client,
                        prompt_template=prompt_template,
                        manifest_sha256=manifest_sha256,
                        prompt_sha256=prompt_sha256,
                    ): item
                    for item in items_to_process
                }

                for future in concurrent.futures.as_completed(future_to_item):
                    item = future_to_item[future]
                    try:
                        results.append(future.result())
                    except Exception as exc:
                        logging.error("Unexpected worker failure for article %s: %s", item["article_id"], exc)
                        record = build_failure_record(
                            config=config,
                            manifest_row=item["manifest_row"],
                            article_id=item["article_id"],
                            article_file=None,
                            output_path=item["output_path"],
                            error_type="unexpected_worker_failure",
                            error=str(exc),
                        )
                        try:
                            write_json_file(item["output_path"], record)
                        except Exception:
                            pass
                        results.append(record)

        run_end = utc_now_iso()
        run_manifest = write_run_outputs(
            config=config,
            manifest_rows_total=manifest_rows_total,
            planned_items=planned_items,
            results=results,
            manifest_sha256=manifest_sha256,
            prompt_sha256=prompt_sha256,
            environment_metadata=environment_metadata,
            run_start=run_start,
            run_end=run_end,
        )

        counts = run_manifest["counts"]
        logging.info(
            "Finished run_id=%s succeeded=%s failed=%s invalid=%s skipped=%s",
            config.run_id,
            counts["articles_succeeded"],
            counts["articles_failed"],
            counts["articles_invalid_response"],
            counts["articles_skipped_existing"],
        )

        if counts["articles_failed"] > 0 or counts["articles_invalid_response"] > 0:
            return 1

        return 0

    except KeyboardInterrupt:
        logging.error("Interrupted by user")
        return 130

    except Exception as exc:
        try:
            config.output.mkdir(parents=True, exist_ok=True)
            if not logging.getLogger().handlers:
                setup_logging(config)
        except Exception:
            pass

        logging.error("Fatal error: %s", exc)
        logging.debug("Fatal traceback:\n%s", traceback.format_exc())

        run_end = utc_now_iso()
        fatal_manifest = {
            "run_id": config.run_id,
            "programme": PROGRAMME_NAME,
            "start_time": run_start,
            "end_time": run_end,
            "status": "failed",
            "error": str(exc),
            "paths": {
                "manifest": relpath(config.manifest, config.script_dir),
                "output": relpath(config.output, config.script_dir),
                "prompt": relpath(config.prompt, config.script_dir),
                "log_file": relpath(config.log_file, config.script_dir),
                "manifest_file": relpath(config.manifest_file, config.script_dir),
                "timestamped_manifest_file": relpath(config.timestamped_manifest_file, config.script_dir),
            },
        }

        try:
            write_json_file(config.manifest_file, fatal_manifest)
            write_json_file(config.timestamped_manifest_file, fatal_manifest)
        except Exception:
            pass

        return 1


if __name__ == "__main__":
    raise SystemExit(main())