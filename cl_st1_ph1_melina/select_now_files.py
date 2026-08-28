#!/usr/bin/env python3
"""
select_now_files.py

Process a dataset directory recursively, filtering all .txt files for lines
that contain any configured search term as a whole word, case-insensitive.
Matching lines are written to same-named UTF-8 text files in their corresponding
subdirectories in the output directory using LF line endings.

Usage:
    python select_now_files.py \
        --input INPUT_DIR \
        --output OUTPUT_DIR
"""

from __future__ import annotations

import argparse
import logging
import re
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
        description="Recursively filter text files by whole-word terms and preserve directory structure."
    )
    parser.add_argument("--input", required=True, help="Input directory")
    parser.add_argument("--output", required=True, help="Output directory")
    return parser.parse_args()


def build_term_pattern(terms: Iterable[str]) -> re.Pattern[str]:
    escaped = [re.escape(term) for term in terms if term]
    if not escaped:
        raise ValueError("SEARCH_TERMS must contain at least one non-empty term.")
    # Match whole words, case-insensitive.
    # Logic uses OR behavior across items due to the join with '|'
    return re.compile(r"\b(?:%s)\b" % "|".join(escaped), re.IGNORECASE)


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def filter_text_file(
        source: Path,
        input_dir: Path,
        output_dir: Path,
        pattern: re.Pattern[str],
        logger: logging.Logger
) -> None:
    try:
        matched_lines: list[str] = []
        with source.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            for line in handle:
                if pattern.search(line):
                    matched_lines.append(line.rstrip("\r\n"))
    except OSError as exc:
        logger.error("Failed to read text file %s: %s", source, exc)
        return

    if not matched_lines:
        logger.info("No matches found in %s; skipping output file", source.name)
        return

    try:
        rel_path = source.relative_to(input_dir)
        output_path = output_dir / rel_path

        # Ensure the target subdirectory exists
        ensure_directory(output_path.parent)

        with output_path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(matched_lines))
            handle.write("\n")
        logger.info("Wrote %d matching line(s) to %s", len(matched_lines), output_path)
    except OSError as exc:
        logger.error("Failed to write output file for %s: %s", source, exc)


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

    # Process all .txt files in the input directory and its subdirectories
    text_files = sorted(input_dir.rglob("*.txt"))
    logger.info("Found %d text file(s) to process", len(text_files))

    for text_file in text_files:
        if text_file.is_file():
            filter_text_file(text_file, input_dir, output_dir, pattern, logger)

    logger.info("Processing complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())