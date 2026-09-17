#!/usr/bin/env python3
"""
Generate plaintext representative examples for LMDA factor interpretation.

This version is adapted for the Melina Phase 2 / Phase 3 NOW corpus layout.

Expected project layout, when run from a phase directory such as
cl_st1_ph2_melina/ or cl_st1_ph3_melina/:

    file_ids.txt
    corpus/05_tagged/<group>/<article_id>.txt
    corpus/04_now_screened_iqr_cap/<group>/<country_code>/<article_id>.txt
    corpus/04_now_screened_iqr/<group>/<country_code>/<article_id>.txt
    sas/output_<project>/<project>_scores_only.tsv
    sas/output_<project>/means_group_f1.tsv
    sas/output_<project>/means_group_f2.tsv
    ...

The tagged corpus is flat below group because country_code is not needed for
the analysis. The full-text corpus retains country_code as a second-level
directory below group, so full-text lookup supports:

    <fulltext_root>/<group>/*/<article_id>.txt

The script writes human-readable .txt files to examples_txt/.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


DEFAULT_PROJECT = Path.cwd().name
DEFAULT_TAGGED_BASE = Path("corpus/05_tagged")
DEFAULT_FILE_IDS_PATH = Path("file_ids.txt")
DEFAULT_SCORE_DETAILS = Path("examples/score_details.txt")
DEFAULT_OUT_ROOT = Path("examples_txt")
DEFAULT_GROUP_COLUMN = "group"

FACTOR_COLUMN_PATTERN = re.compile(r"^fac(\d+)$", re.IGNORECASE)
TEXT_ID_PATTERN = re.compile(r"^t\d+$", re.IGNORECASE)


@dataclass(frozen=True)
class ExampleRecord:
    factor_number: int
    factor_column: str
    pole: str
    group: str
    filename: str
    score: float
    group_mean: float | None
    tagged_path: Path | None
    fulltext_path: Path | None
    output_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate plaintext representative examples by factor pole and group."
        )
    )

    parser.add_argument(
        "--project",
        default=DEFAULT_PROJECT,
        help=f"Project name. Default: current directory name ({DEFAULT_PROJECT!r}).",
    )

    parser.add_argument(
        "--sas-output",
        type=Path,
        default=None,
        help=(
            "Directory containing SAS TSV outputs. If omitted, the script tries "
            "sas/output_<project>, sas/, and selected fallback locations."
        ),
    )

    parser.add_argument(
        "--scores",
        type=Path,
        default=None,
        help=(
            "Path to the SAS scores TSV file. If omitted, the script looks for "
            "<project>_scores_only.tsv, then <project>_scores.tsv."
        ),
    )

    parser.add_argument(
        "--means-prefix",
        default=None,
        help=(
            "Prefix for means files. Default is derived from --group-column, "
            "e.g. means_group_f for group."
        ),
    )

    parser.add_argument(
        "--group-column",
        default=DEFAULT_GROUP_COLUMN,
        help="Grouping column in the SAS scores/means outputs. Default: group.",
    )

    parser.add_argument(
        "--tagged-base",
        type=Path,
        default=DEFAULT_TAGGED_BASE,
        help=f"Tagged corpus root. Default: {DEFAULT_TAGGED_BASE}.",
    )

    parser.add_argument(
        "--fulltext-root",
        type=Path,
        default=None,
        help=(
            "Original full-text corpus root. If omitted, the script tries "
            "corpus/04_now_screened_iqr_cap and corpus/04_now_screened_iqr."
        ),
    )

    parser.add_argument(
        "--file-ids",
        type=Path,
        default=DEFAULT_FILE_IDS_PATH,
        help=f"Path to file_ids.txt. Default: {DEFAULT_FILE_IDS_PATH}.",
    )

    parser.add_argument(
        "--score-details",
        type=Path,
        default=DEFAULT_SCORE_DETAILS,
        help=(
            "Optional score-details report used to add present loading words "
            f"where parseable. Default: {DEFAULT_SCORE_DETAILS}."
        ),
    )

    parser.add_argument(
        "--out-root",
        type=Path,
        default=DEFAULT_OUT_ROOT,
        help=f"Output directory. Default: {DEFAULT_OUT_ROOT}.",
    )

    parser.add_argument(
        "--factors",
        type=str,
        default=None,
        help=(
            "Comma-separated factor numbers to process, e.g. 1,2,5. "
            "If omitted, all facN columns in the scores file are used."
        ),
    )

    parser.add_argument(
        "--groups-per-pole",
        type=int,
        default=3,
        help=(
            "Number of highest/lowest mean groups to sample per factor pole. "
            "Default: 3."
        ),
    )

    parser.add_argument(
        "--examples-per-group",
        type=int,
        default=3,
        help="Number of texts to select per group and pole. Default: 3.",
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=12000,
        help=(
            "Maximum number of characters of article text to write per example. "
            "Use 0 for no truncation. Default: 12000."
        ),
    )

    parser.add_argument(
        "--prefer-fulltext",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Use original full text when available; otherwise use tagged text. "
            "Default: true."
        ),
    )

    parser.add_argument(
        "--clean-output",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Delete the output directory before writing. Default: true.",
    )

    parser.add_argument(
        "--extract-sas-zip",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "If sas/output_<project> is absent, extract output_<project>.zip "
            "when found. Default: true."
        ),
    )

    return parser.parse_args()


def resolve_sas_output_dir(
    project: str,
    requested: Path | None,
    extract_sas_zip: bool,
) -> Path:
    if requested is not None:
        if not requested.exists():
            raise FileNotFoundError(f"SAS output directory does not exist: {requested}")
        if not requested.is_dir():
            raise NotADirectoryError(f"SAS output path is not a directory: {requested}")
        return requested

    preferred = Path("sas") / f"output_{project}"

    if preferred.is_dir():
        return preferred

    if extract_sas_zip:
        zip_candidates = [
            Path("sas") / f"output_{project}.zip",
            Path("sas") / "zip" / f"output_{project}.zip",
            Path("zip") / f"output_{project}.zip",
            Path(f"output_{project}.zip"),
        ]

        for zip_path in zip_candidates:
            if zip_path.is_file():
                preferred.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(zip_path, "r") as archive:
                    archive.extractall(preferred)
                return preferred

    candidates = [
        Path("sas"),
        Path("."),
    ]

    for candidate in candidates:
        if candidate.is_dir() and any(candidate.glob(f"{project}_scores*.tsv")):
            return candidate

    raise FileNotFoundError(
        "Could not locate SAS output directory. Tried "
        f"{preferred}, sas/, and current directory. "
        "Use --sas-output or --scores to specify files explicitly."
    )


def resolve_scores_path(project: str, sas_output_dir: Path, requested: Path | None) -> Path:
    if requested is not None:
        if not requested.exists():
            raise FileNotFoundError(f"Scores file does not exist: {requested}")
        return requested

    candidates = [
        sas_output_dir / f"{project}_scores_only.tsv",
        sas_output_dir / f"{project}_scores.tsv",
        Path("sas") / f"{project}_scores_only.tsv",
        Path("sas") / f"{project}_scores.tsv",
        Path(f"{project}_scores_only.tsv"),
        Path(f"{project}_scores.tsv"),
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    found = sorted(sas_output_dir.glob("*_scores_only.tsv"))
    if found:
        return found[0]

    found = sorted(sas_output_dir.glob("*_scores.tsv"))
    if found:
        return found[0]

    raise FileNotFoundError(
        f"Could not locate scores TSV for project {project!r} in {sas_output_dir}."
    )


def resolve_fulltext_root(requested: Path | None) -> Path | None:
    if requested is not None:
        if not requested.exists():
            raise FileNotFoundError(f"Full-text root does not exist: {requested}")
        if not requested.is_dir():
            raise NotADirectoryError(f"Full-text root is not a directory: {requested}")
        return requested

    candidates = [
        Path("corpus/04_now_screened_iqr_cap"),
        Path("corpus/04_now_screened_iqr"),
        Path("corpus/02_now_organised"),
    ]

    for candidate in candidates:
        if candidate.is_dir():
            return candidate

    return None


def natural_sort_key(value: object) -> list[object]:
    text = str(value)
    parts = re.split(r"(\d+)", text)
    key: list[object] = []

    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part.lower())

    return key


def parse_factor_numbers(raw: str | None) -> set[int] | None:
    if raw is None or not raw.strip():
        return None

    factors: set[int] = set()

    for item in raw.split(","):
        item = item.strip()

        if not item:
            continue

        if not item.isdigit():
            raise ValueError(f"Invalid factor number in --factors: {item!r}")

        factors.add(int(item))

    return factors


def detect_factor_columns(df: pd.DataFrame) -> list[str]:
    factor_columns: list[tuple[int, str]] = []

    for column in df.columns:
        match = FACTOR_COLUMN_PATTERN.match(str(column))

        if match:
            factor_columns.append((int(match.group(1)), str(column)))

    factor_columns.sort(key=lambda item: item[0])
    return [column for _, column in factor_columns]


def factor_number_from_column(column: str) -> int:
    match = FACTOR_COLUMN_PATTERN.match(column)

    if match is None:
        raise ValueError(f"Not a factor column: {column}")

    return int(match.group(1))


def load_id_map(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"file_ids path does not exist: {path}")

    id_map: dict[str, str] = {}

    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()

            if not stripped:
                continue

            if line_number == 1 and stripped.lower().startswith("filename"):
                continue

            if "\t" in stripped:
                parts = stripped.split("\t")
            else:
                parts = stripped.split()

            if len(parts) < 2:
                continue

            text_id = parts[0].strip()
            relative_path = parts[-1].strip()

            if not TEXT_ID_PATTERN.match(text_id):
                continue

            id_map[text_id] = relative_path.replace("\\", "/")

    if not id_map:
        raise ValueError(f"No text-id mappings could be read from {path}")

    return id_map


def locate_tagged_text(
    row: pd.Series,
    id_map: dict[str, str],
    tagged_base: Path,
    group_column: str,
) -> Path | None:
    text_id = str(row["filename"])
    relative_path = id_map.get(text_id)

    if relative_path:
        direct_path = tagged_base / relative_path

        if direct_path.exists():
            return direct_path

        relative = Path(relative_path)
        article_filename = relative.name

        if group_column in row and pd.notna(row[group_column]):
            group = str(row[group_column]).strip()
            grouped_path = tagged_base / group / article_filename

            if grouped_path.exists():
                return grouped_path

    if group_column in row and pd.notna(row[group_column]):
        group = str(row[group_column]).strip()

        if relative_path:
            article_filename = Path(relative_path).name
            grouped_path = tagged_base / group / article_filename

            if grouped_path.exists():
                return grouped_path

    return None


def locate_fulltext(
    row: pd.Series,
    id_map: dict[str, str],
    fulltext_root: Path | None,
    group_column: str,
) -> Path | None:
    if fulltext_root is None:
        return None

    text_id = str(row["filename"])
    relative_path = id_map.get(text_id)

    if not relative_path:
        return None

    direct_path = fulltext_root / relative_path

    if direct_path.exists():
        return direct_path

    relative = Path(relative_path)
    article_filename = relative.name

    if group_column in row and pd.notna(row[group_column]):
        group = str(row[group_column]).strip()
    elif len(relative.parts) >= 2:
        group = relative.parts[0]
    else:
        return None

    group_dir = fulltext_root / group

    if not group_dir.is_dir():
        return None

    matches = sorted(group_dir.glob(f"*/{article_filename}"))

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple full-text matches found for {text_id} / {article_filename}: "
            + ", ".join(str(path) for path in matches)
        )

    recursive_matches = sorted(fulltext_root.rglob(article_filename))

    if len(recursive_matches) == 1:
        return recursive_matches[0]

    if len(recursive_matches) > 1:
        same_group = [
            path for path in recursive_matches
            if len(path.relative_to(fulltext_root).parts) >= 2
            and path.relative_to(fulltext_root).parts[0] == group
        ]

        if len(same_group) == 1:
            return same_group[0]

        raise RuntimeError(
            f"Multiple recursive full-text matches found for {text_id} / "
            f"{article_filename}: "
            + ", ".join(str(path) for path in recursive_matches)
        )

    return None


def read_text(path: Path | None) -> str:
    if path is None:
        return ""

    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def truncate_text(text: str, max_chars: int) -> tuple[str, bool]:
    if max_chars <= 0:
        return text, False

    if len(text) <= max_chars:
        return text, False

    return text[:max_chars].rstrip() + "\n\n[Text truncated]\n", True


def read_decade_means(
    sas_output_dir: Path,
    factor_number: int,
    group_column: str,
    means_prefix: str,
) -> pd.DataFrame | None:
    path = sas_output_dir / f"{means_prefix}{factor_number}.tsv"

    if not path.exists():
        return None

    df = pd.read_csv(path, sep="\t")

    if df.empty:
        return None

    if group_column not in df.columns:
        matching_columns = [
            column for column in df.columns
            if str(column).lower() == group_column.lower()
        ]

        if matching_columns:
            df = df.rename(columns={matching_columns[0]: group_column})
        else:
            return None

    mean_column = None

    for candidate in ["Mean", "mean", "MEAN"]:
        if candidate in df.columns:
            mean_column = candidate
            break

    if mean_column is None:
        factor_column = f"fac{factor_number}"

        if factor_column in df.columns:
            mean_column = factor_column

    if mean_column is None:
        possible = [
            column for column in df.columns
            if "mean" in str(column).lower()
        ]

        if possible:
            mean_column = possible[0]

    if mean_column is None:
        numeric_columns = [
            column for column in df.columns
            if column != group_column and pd.api.types.is_numeric_dtype(df[column])
        ]

        if numeric_columns:
            mean_column = numeric_columns[-1]

    if mean_column is None:
        return None

    result = df[[group_column, mean_column]].copy()
    result = result.rename(columns={mean_column: "mean"})
    result[group_column] = result[group_column].astype(str)
    result["mean"] = pd.to_numeric(result["mean"], errors="coerce")
    result = result.dropna(subset=["mean"])

    if result.empty:
        return None

    return result


def compute_group_means_from_scores(
    scores_df: pd.DataFrame,
    factor_column: str,
    group_column: str,
) -> pd.DataFrame:
    result = (
        scores_df
        .groupby(group_column, dropna=False)[factor_column]
        .mean()
        .reset_index()
        .rename(columns={factor_column: "mean"})
    )
    result[group_column] = result[group_column].astype(str)
    result["mean"] = pd.to_numeric(result["mean"], errors="coerce")
    result = result.dropna(subset=["mean"])
    return result


def selected_groups_for_pole(
    means_df: pd.DataFrame,
    pole: str,
    group_column: str,
    groups_per_pole: int,
) -> list[tuple[str, float]]:
    ascending = pole == "neg"

    sorted_df = means_df.sort_values(
        by=["mean", group_column],
        ascending=[ascending, True],
        key=None,
    )

    selected = sorted_df.head(groups_per_pole)
    return [
        (str(row[group_column]), float(row["mean"]))
        for _, row in selected.iterrows()
    ]


def parse_score_details(path: Path) -> dict[tuple[str, int], dict[str, list[str]]]:
    """
    Best-effort parser for examples/score_details.txt.

    Because score-details reports vary across projects, this parser is deliberately
    permissive. It recognises t-prefixed text ids, facN labels, and lines naming
    positive/negative loading words.

    Returns:
        {
            ("t000001", 1): {
                "positive": ["word1", "word2"],
                "negative": ["word3"],
            }
        }
    """
    if not path.exists():
        return {}

    details: dict[tuple[str, int], dict[str, list[str]]] = {}
    current_text_id: str | None = None
    current_factor: int | None = None

    text_id_re = re.compile(r"\b(t\d+)\b", re.IGNORECASE)
    factor_re = re.compile(r"\bfac(?:tor)?\s*[-_:]?\s*(\d+)\b", re.IGNORECASE)
    bracket_list_re = re.compile(r"\[([^\]]*)\]")

    def clean_words(raw: str) -> list[str]:
        raw = raw.strip()

        if not raw:
            return []

        bracket_match = bracket_list_re.search(raw)

        if bracket_match:
            raw = bracket_match.group(1)

        raw = raw.replace(";", ",")
        parts = re.split(r"[,\s]+", raw)
        words: list[str] = []

        for part in parts:
            word = part.strip().strip("'\"`.,;:()[]{}")

            if not word:
                continue

            if word.lower() in {
                "none",
                "positive",
                "negative",
                "pos",
                "neg",
                "words",
                "loading",
                "loadings",
                "present",
            }:
                continue

            if re.search(r"[A-Za-z]", word):
                words.append(word)

        return words

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()

            if not stripped:
                continue

            text_match = text_id_re.search(stripped)

            if text_match:
                current_text_id = text_match.group(1).lower()

            factor_match = factor_re.search(stripped)

            if factor_match:
                current_factor = int(factor_match.group(1))

            if current_text_id is None or current_factor is None:
                continue

            lower = stripped.lower()
            key = (current_text_id, current_factor)

            if key not in details:
                details[key] = {"positive": [], "negative": []}

            if "positive" in lower or re.search(r"\bpos\b", lower):
                after_separator = re.split(r"[:=]", stripped, maxsplit=1)
                raw_words = after_separator[-1] if len(after_separator) > 1 else stripped
                details[key]["positive"].extend(clean_words(raw_words))

            elif "negative" in lower or re.search(r"\bneg\b", lower):
                after_separator = re.split(r"[:=]", stripped, maxsplit=1)
                raw_words = after_separator[-1] if len(after_separator) > 1 else stripped
                details[key]["negative"].extend(clean_words(raw_words))

    for key, value in details.items():
        value["positive"] = sorted(set(value["positive"]), key=natural_sort_key)
        value["negative"] = sorted(set(value["negative"]), key=natural_sort_key)

    return details


def safe_filename(value: object) -> str:
    text = str(value).strip()
    text = re.sub(r"[^\w.-]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_") or "unknown"


def format_words(words: Iterable[str]) -> str:
    words = list(words)

    if not words:
        return "(none found or unavailable)"

    return ", ".join(words)


def make_output_path(
    out_root: Path,
    factor_number: int,
    pole: str,
    group: str,
    rank: int,
    filename: str,
) -> Path:
    return (
        out_root
        / f"fac{factor_number}"
        / pole
        / safe_filename(group)
        / f"{rank:02d}_{safe_filename(filename)}.txt"
    )


def write_plaintext_example(
    record: ExampleRecord,
    text: str,
    source_kind: str,
    score_details: dict[tuple[str, int], dict[str, list[str]]],
    max_chars: int,
) -> None:
    record.output_path.parent.mkdir(parents=True, exist_ok=True)

    text, truncated = truncate_text(text, max_chars=max_chars)

    detail = score_details.get((record.filename.lower(), record.factor_number), {})
    positive_words = detail.get("positive", [])
    negative_words = detail.get("negative", [])

    group_mean_text = (
        f"{record.group_mean:.6f}"
        if record.group_mean is not None
        else "unavailable"
    )

    tagged_path_text = str(record.tagged_path) if record.tagged_path else "not found"
    fulltext_path_text = str(record.fulltext_path) if record.fulltext_path else "not found"

    header = [
        "=" * 80,
        "LMDA PLAINTEXT EXAMPLE",
        "=" * 80,
        f"Factor: fac{record.factor_number}",
        f"Pole: {record.pole}",
        f"Group: {record.group}",
        f"Text ID: {record.filename}",
        f"Text score: {record.score:.6f}",
        f"Group mean for factor: {group_mean_text}",
        f"Text source used: {source_kind}",
        f"Tagged path: {tagged_path_text}",
        f"Full-text path: {fulltext_path_text}",
        f"Truncated: {'yes' if truncated else 'no'}",
        "",
        "Present positive-pole loading words:",
        format_words(positive_words),
        "",
        "Present negative-pole loading words:",
        format_words(negative_words),
        "",
        "=" * 80,
        "TEXT",
        "=" * 80,
        "",
    ]

    record.output_path.write_text(
        "\n".join(header) + text.rstrip() + "\n",
        encoding="utf-8",
    )


def write_index(records: list[ExampleRecord], out_root: Path) -> None:
    index_path = out_root / "index.tsv"
    index_path.parent.mkdir(parents=True, exist_ok=True)

    with index_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "factor",
                "pole",
                "group",
                "filename",
                "score",
                "group_mean",
                "tagged_path",
                "fulltext_path",
                "output_path",
            ]
        )

        for record in records:
            writer.writerow(
                [
                    f"fac{record.factor_number}",
                    record.pole,
                    record.group,
                    record.filename,
                    f"{record.score:.6f}",
                    "" if record.group_mean is None else f"{record.group_mean:.6f}",
                    "" if record.tagged_path is None else str(record.tagged_path),
                    "" if record.fulltext_path is None else str(record.fulltext_path),
                    str(record.output_path),
                ]
            )


def validate_scores_df(
    df: pd.DataFrame,
    group_column: str,
    factor_columns: list[str],
) -> None:
    required_columns = ["filename", group_column]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Scores file is missing required column(s): "
            + ", ".join(missing)
        )

    if not factor_columns:
        raise ValueError("No factor columns matching facN were found in scores file.")


def select_examples_for_group(
    scores_df: pd.DataFrame,
    factor_column: str,
    group_column: str,
    group: str,
    pole: str,
    examples_per_group: int,
) -> pd.DataFrame:
    subset = scores_df[scores_df[group_column].astype(str) == group].copy()

    if subset.empty:
        return subset

    subset[factor_column] = pd.to_numeric(subset[factor_column], errors="coerce")
    subset = subset.dropna(subset=[factor_column])

    if subset.empty:
        return subset

    ascending = pole == "neg"

    subset = subset.sort_values(
        by=[factor_column, "filename"],
        ascending=[ascending, True],
    )

    return subset.head(examples_per_group)


def main() -> int:
    args = parse_args()

    means_prefix = (
        args.means_prefix
        if args.means_prefix is not None
        else f"means_{args.group_column}_f"
    )

    requested_factors = parse_factor_numbers(args.factors)

    sas_output_dir = resolve_sas_output_dir(
        project=args.project,
        requested=args.sas_output,
        extract_sas_zip=args.extract_sas_zip,
    )

    scores_path = resolve_scores_path(
        project=args.project,
        sas_output_dir=sas_output_dir,
        requested=args.scores,
    )

    fulltext_root = resolve_fulltext_root(args.fulltext_root)

    if not args.tagged_base.is_dir():
        raise FileNotFoundError(f"Tagged corpus root does not exist: {args.tagged_base}")

    id_map = load_id_map(args.file_ids)

    scores_df = pd.read_csv(scores_path, sep="\t")
    scores_df.columns = [str(column).strip() for column in scores_df.columns]

    factor_columns = detect_factor_columns(scores_df)

    if requested_factors is not None:
        factor_columns = [
            column for column in factor_columns
            if factor_number_from_column(column) in requested_factors
        ]

    validate_scores_df(
        df=scores_df,
        group_column=args.group_column,
        factor_columns=factor_columns,
    )

    scores_df["filename"] = scores_df["filename"].astype(str)
    scores_df[args.group_column] = scores_df[args.group_column].astype(str)

    for factor_column in factor_columns:
        scores_df[factor_column] = pd.to_numeric(
            scores_df[factor_column],
            errors="coerce",
        )

    score_details = parse_score_details(args.score_details)

    if args.clean_output and args.out_root.exists():
        shutil.rmtree(args.out_root)

    args.out_root.mkdir(parents=True, exist_ok=True)

    records: list[ExampleRecord] = []
    missing_text_count = 0

    print(f"Project: {args.project}")
    print(f"SAS output: {sas_output_dir}")
    print(f"Scores file: {scores_path}")
    print(f"Tagged base: {args.tagged_base}")
    print(f"Full-text root: {fulltext_root if fulltext_root else 'not found'}")
    print(f"Output root: {args.out_root}")
    print(f"Group column: {args.group_column}")
    print(f"Means prefix: {means_prefix}")
    print(f"Factors: {', '.join(factor_columns)}")
    print()

    for factor_column in factor_columns:
        factor_number = factor_number_from_column(factor_column)

        means_df = read_decade_means(
            sas_output_dir=sas_output_dir,
            factor_number=factor_number,
            group_column=args.group_column,
            means_prefix=means_prefix,
        )

        if means_df is None:
            means_df = compute_group_means_from_scores(
                scores_df=scores_df,
                factor_column=factor_column,
                group_column=args.group_column,
            )

        print(f"Processing fac{factor_number}")

        for pole in ["pos", "neg"]:
            selected_groups = selected_groups_for_pole(
                means_df=means_df,
                pole=pole,
                group_column=args.group_column,
                groups_per_pole=args.groups_per_pole,
            )

            print(
                f"  {pole}: "
                + ", ".join(
                    f"{group} ({mean:.4f})"
                    for group, mean in selected_groups
                )
            )

            for group, group_mean in selected_groups:
                selected_examples = select_examples_for_group(
                    scores_df=scores_df,
                    factor_column=factor_column,
                    group_column=args.group_column,
                    group=group,
                    pole=pole,
                    examples_per_group=args.examples_per_group,
                )

                for rank, (_, row) in enumerate(selected_examples.iterrows(), start=1):
                    filename = str(row["filename"])
                    score = float(row[factor_column])

                    tagged_path = locate_tagged_text(
                        row=row,
                        id_map=id_map,
                        tagged_base=args.tagged_base,
                        group_column=args.group_column,
                    )

                    fulltext_path = locate_fulltext(
                        row=row,
                        id_map=id_map,
                        fulltext_root=fulltext_root,
                        group_column=args.group_column,
                    )

                    if args.prefer_fulltext and fulltext_path is not None:
                        text_path = fulltext_path
                        source_kind = "fulltext"
                    else:
                        text_path = tagged_path
                        source_kind = "tagged"

                    if text_path is None:
                        missing_text_count += 1
                        continue

                    text = read_text(text_path)

                    if not text.strip():
                        missing_text_count += 1
                        continue

                    output_path = make_output_path(
                        out_root=args.out_root,
                        factor_number=factor_number,
                        pole=pole,
                        group=group,
                        rank=rank,
                        filename=filename,
                    )

                    record = ExampleRecord(
                        factor_number=factor_number,
                        factor_column=factor_column,
                        pole=pole,
                        group=group,
                        filename=filename,
                        score=score,
                        group_mean=group_mean,
                        tagged_path=tagged_path,
                        fulltext_path=fulltext_path,
                        output_path=output_path,
                    )

                    write_plaintext_example(
                        record=record,
                        text=text,
                        source_kind=source_kind,
                        score_details=score_details,
                        max_chars=args.max_chars,
                    )

                    records.append(record)

    write_index(records, args.out_root)

    print()
    print(f"Examples written: {len(records)}")
    print(f"Missing/unreadable selected texts: {missing_text_count}")
    print(f"Index written to: {args.out_root / 'index.tsv'}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)