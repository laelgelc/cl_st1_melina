#!/usr/bin/env python3
"""
select_now_files.py

Process a dataset directory by extracting supported archives, then filtering all
text files for lines that contain any configured search term as a whole word,
case-insensitive.

Usage:
    python select_now_files.py \
        --input INPUT_DIR \
        --output OUTPUT_DIR

The script keeps original zip files, extracts tar files first, extracts zip
files into the input directory root, flattens archived paths into the first
level, and writes matched lines to same-named UTF-8 text files in the output
directory using LF line endings.
"""

from __future__ import annotations

import argparse
import logging
import re
import tarfile
import zipfile
from pathlib import Path
from typing import Iterable


SEARCH_TERMS = [
    "gaza",
]


def configure_logging(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("select_now_files")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract archives from an input directory and filter text files by whole-word terms."
    )
    parser.add_argument("--input", required=True, help="Input directory")
    parser.add_argument("--output", required=True, help="Output directory")
    return parser.parse_args()


def build_term_pattern(terms: Iterable[str]) -> re.Pattern[str]:
    escaped = [re.escape(term) for term in terms if term]
    if not escaped:
        raise ValueError("SEARCH_TERMS must contain at least one non-empty term.")
    return re.compile(r"\b(?:%s)\b" % "|".join(escaped), re.IGNORECASE)


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def unique_target_path(directory: Path, filename: str, logger: logging.Logger) -> Path | None:
    target = directory / filename
    if target.exists():
        logger.info("Skipping duplicate file name already present: %s", filename)
        return None
    return target


def extract_tar_archives(input_dir: Path, logger: logging.Logger) -> None:
    tar_files = sorted(input_dir.glob("*.tar"))
    for tar_path in tar_files:
        logger.info("Extracting tar archive: %s", tar_path.name)
        try:
            with tarfile.open(tar_path, "r:*") as tf:
                tf.extractall(path=input_dir, filter="data")
        except (tarfile.TarError, OSError, ValueError) as exc:
            logger.error("Failed to extract tar archive %s: %s", tar_path.name, exc)


def extract_zip_archives(input_dir: Path, logger: logging.Logger) -> None:
    zip_files = sorted(input_dir.glob("*.zip"))
    for zip_path in zip_files:
        logger.info("Extracting zip archive into input root: %s", zip_path.name)
        try:
            with zipfile.ZipFile(zip_path) as zf:
                for member in zf.infolist():
                    if member.is_dir():
                        continue

                    original_name = member.filename
                    flattened_name = Path(original_name).name

                    if not flattened_name:
                        logger.warning("Skipping zip member with empty filename in %s", zip_path.name)
                        continue

                    if "/" in original_name or "\\" in original_name:
                        logger.info(
                            "Flattening archived path to first-level filename: %s -> %s",
                            original_name,
                            flattened_name,
                        )

                    target = unique_target_path(input_dir, flattened_name, logger)
                    if target is None:
                        continue

                    try:
                        with zf.open(member) as source, target.open("wb") as dest:
                            dest.write(source.read())
                    except OSError as exc:
                        logger.error(
                            "Failed to extract member %s from %s: %s",
                            original_name,
                            zip_path.name,
                            exc,
                        )
        except (zipfile.BadZipFile, OSError) as exc:
            logger.error("Failed to extract zip archive %s: %s", zip_path.name, exc)


def iter_text_files(input_dir: Path) -> list[Path]:
    return sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() == ".txt"
    )


def filter_text_file(source: Path, output_dir: Path, pattern: re.Pattern[str], logger: logging.Logger) -> None:
    try:
        matched_lines: list[str] = []
        with source.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            for line in handle:
                if pattern.search(line):
                    matched_lines.append(line.rstrip("\r\n"))
    except OSError as exc:
        logger.error("Failed to read text file %s: %s", source.name, exc)
        return

    if not matched_lines:
        logger.info("No matches found in %s; skipping output file", source.name)
        return

    output_path = output_dir / source.name
    try:
        with output_path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(matched_lines))
            handle.write("\n")
        logger.info("Wrote %d matching line(s) to %s", len(matched_lines), output_path.name)
    except OSError as exc:
        logger.error("Failed to write output file %s: %s", output_path.name, exc)


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    script_dir = Path(__file__).resolve().parent

    ensure_directory(output_dir)
    logger = configure_logging(script_dir / "select_now_files.log")

    if not input_dir.exists() or not input_dir.is_dir():
        logger.error("Input directory does not exist or is not a directory: %s", input_dir)
        return 1

    try:
        pattern = build_term_pattern(SEARCH_TERMS)
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    logger.info("Starting processing for input=%s output=%s", input_dir, output_dir)

    extract_tar_archives(input_dir, logger)
    extract_zip_archives(input_dir, logger)

    text_files = iter_text_files(input_dir)
    logger.info("Found %d text file(s) to process", len(text_files))

    for text_file in text_files:
        filter_text_file(text_file, output_dir, pattern, logger)

    logger.info("Processing complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())