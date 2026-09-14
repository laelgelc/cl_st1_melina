#!/usr/bin/env python3
"""
find_now_sources_text_matches.py

Match selected NOW corpus article text files with their corresponding NOW source
metadata rows.

The programme recursively scans selected article text files, extracts article IDs
from lines beginning with '@@', then streams large NOW source metadata files line
by line to find matching article IDs. Matched metadata rows are filtered by an
inclusive publication date range and written to a consolidated TSV file.

Usage:
    python find_now_sources_text_matches.py \
        --initial-date 2020-01-01 \
        --final-date 2020-12-31 \
        --input-sources corpus/01_now_dataset_raw/01_now_sources_raw \
        --input-articles corpus/01_now_dataset/02_now_text \
        --match corpus/01_now_dataset/01_now_matched_sources
"""

from __future__ import annotations

import argparse
import csv
import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


ARTICLE_ID_PATTERN = re.compile(r"^\s*@@(\d+)\b")

MATCHED_SOURCES_FILENAME = "matched_sources.tsv"
UNMATCHED_ARTICLE_IDS_FILENAME = "unmatched_article_ids.tsv"
DUPLICATE_ARTICLE_IDS_FILENAME = "duplicate_article_ids.tsv"
DUPLICATE_METADATA_MATCHES_FILENAME = "duplicate_metadata_matches.tsv"
LOG_FILENAME = "find_now_sources_text_matches.log"


@dataclass
class ArticleIdCollectionResult:
    selected_article_locations: dict[str, list[str]] = field(default_factory=dict)
    article_files_found: int = 0
    article_lines_scanned: int = 0
    article_ids_found: int = 0
    malformed_article_lines: int = 0
    unreadable_article_files: int = 0


@dataclass
class MetadataScanResult:
    matched_ids: set[str] = field(default_factory=set)
    metadata_match_counts: Counter[str] = field(default_factory=Counter)
    metadata_match_source_files: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    source_files_found: int = 0
    source_lines_scanned: int = 0
    matched_metadata_rows: int = 0
    malformed_metadata_lines: int = 0
    unreadable_source_files: int = 0


@dataclass(frozen=True)
class SourceMetadataRow:
    article_id: str
    now_field_2: str
    date_original: str
    date_iso: str
    country_code: str
    source_name: str
    url: str
    title: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Match selected NOW corpus article IDs with source metadata rows "
            "using an inclusive date range."
        )
    )
    parser.add_argument(
        "--initial-date",
        required=True,
        help="First publication date to include, in ISO format: YYYY-MM-DD.",
    )
    parser.add_argument(
        "--final-date",
        required=True,
        help="Final publication date to include, in ISO format: YYYY-MM-DD.",
    )
    parser.add_argument(
        "--input-sources",
        required=True,
        help="Directory containing raw NOW source metadata .txt files.",
    )
    parser.add_argument(
        "--input-articles",
        required=True,
        help="Directory containing selected NOW article text .txt files.",
    )
    parser.add_argument(
        "--match",
        required=True,
        help="Output directory for matched metadata and diagnostic files.",
    )
    return parser.parse_args()


def configure_logging(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("find_now_sources_text_matches")
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


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def parse_iso_date(value: str, argument_name: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{argument_name} must be a valid ISO date in YYYY-MM-DD format: {value}") from exc


def parse_now_date(value: str) -> tuple[date, str]:
    try:
        parsed = datetime.strptime(value, "%y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Invalid NOW date: {value}") from exc

    # datetime.strptime with %y follows a 1969/2068 pivot. The NOW corpus dates
    # used in this project are interpreted explicitly as 2000-based years.
    year_text = value.split("-", maxsplit=1)[0]
    if len(year_text) != 2 or not year_text.isdigit():
        raise ValueError(f"Invalid NOW date year: {value}")

    year = 2000 + int(year_text)
    parsed = date(year, parsed.month, parsed.day)
    return parsed, parsed.isoformat()


def validate_input_directory(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"{label} is not a directory: {path}")


def iter_text_files(input_dir: Path) -> list[Path]:
    return sorted(path for path in input_dir.rglob("*.txt") if path.is_file())


def relative_posix_path(path: Path, base_dir: Path) -> str:
    return path.relative_to(base_dir).as_posix()


def extract_article_id_from_article_line(line: str) -> str | None:
    match = ARTICLE_ID_PATTERN.match(line)
    if match is None:
        return None
    return match.group(1)


def collect_article_ids(input_articles: Path, logger: logging.Logger) -> ArticleIdCollectionResult:
    result = ArticleIdCollectionResult()
    article_locations: dict[str, list[str]] = defaultdict(list)

    article_files = iter_text_files(input_articles)
    result.article_files_found = len(article_files)
    logger.info("Found %d selected article text file(s)", result.article_files_found)

    for article_file in article_files:
        relative_article_file = relative_posix_path(article_file, input_articles)

        try:
            with article_file.open("r", encoding="utf-8", errors="replace", newline="") as handle:
                for line in handle:
                    line = line.rstrip("\r\n")

                    if not line:
                        continue

                    result.article_lines_scanned += 1
                    article_id = extract_article_id_from_article_line(line)

                    if article_id is None:
                        result.malformed_article_lines += 1
                        continue

                    result.article_ids_found += 1
                    article_locations[article_id].append(relative_article_file)

        except OSError as exc:
            result.unreadable_article_files += 1
            logger.error("Failed to read selected article file %s: %s", article_file, exc)

    result.selected_article_locations = dict(article_locations)

    duplicate_article_ids = sum(
        1 for locations in result.selected_article_locations.values()
        if len(locations) > 1
    )

    logger.info("Selected article lines scanned: %d", result.article_lines_scanned)
    logger.info("Selected article IDs found: %d", result.article_ids_found)
    logger.info("Unique selected article IDs: %d", len(result.selected_article_locations))
    logger.info("Duplicate selected article IDs: %d", duplicate_article_ids)

    if result.malformed_article_lines:
        logger.warning("Malformed selected article lines skipped: %d", result.malformed_article_lines)

    if result.unreadable_article_files:
        logger.warning("Unreadable selected article files: %d", result.unreadable_article_files)

    return result


def parse_source_metadata_line(line: str) -> SourceMetadataRow:
    fields = line.rstrip("\r\n").split("\t", 6)

    if len(fields) < 7:
        raise ValueError("Metadata row has fewer than seven tab-separated fields.")

    article_id, now_field_2, date_original, country_code, source_name, url, title = fields

    if not article_id:
        raise ValueError("Metadata row has an empty article ID.")

    _, date_iso = parse_now_date(date_original)

    return SourceMetadataRow(
        article_id=article_id,
        now_field_2=now_field_2,
        date_original=date_original,
        date_iso=date_iso,
        country_code=country_code,
        source_name=source_name,
        url=url,
        title=title,
    )


def extract_metadata_article_id_fast(line: str) -> str | None:
    first_tab_index = line.find("\t")
    if first_tab_index == -1:
        return None

    article_id = line[:first_tab_index]
    if not article_id:
        return None

    return article_id


def write_matched_sources_header(writer: csv.writer) -> None:
    writer.writerow(
        [
            "article_id",
            "now_field_2",
            "date_original",
            "date_iso",
            "country_code",
            "source_name",
            "url",
            "title",
            "article_file",
            "source_file",
        ]
    )


def scan_source_metadata(
    input_sources: Path,
    selected_article_locations: dict[str, list[str]],
    initial_date: date,
    final_date: date,
    matched_sources_path: Path,
    logger: logging.Logger,
) -> MetadataScanResult:
    result = MetadataScanResult()
    selected_ids = set(selected_article_locations)

    source_files = iter_text_files(input_sources)
    result.source_files_found = len(source_files)
    logger.info("Found %d source metadata file(s)", result.source_files_found)

    try:
        with matched_sources_path.open("w", encoding="utf-8", newline="") as output_handle:
            writer = csv.writer(output_handle, delimiter="\t", lineterminator="\n")
            write_matched_sources_header(writer)

            for source_file in source_files:
                relative_source_file = relative_posix_path(source_file, input_sources)
                logger.info("Scanning source metadata file: %s", relative_source_file)

                try:
                    with source_file.open("r", encoding="utf-8", errors="replace", newline="") as input_handle:
                        for line in input_handle:
                            if not line.strip():
                                continue

                            result.source_lines_scanned += 1

                            article_id = extract_metadata_article_id_fast(line)
                            if article_id is None:
                                result.malformed_metadata_lines += 1
                                continue

                            if article_id not in selected_ids:
                                continue

                            try:
                                metadata = parse_source_metadata_line(line)
                                metadata_date = date.fromisoformat(metadata.date_iso)
                            except ValueError:
                                result.malformed_metadata_lines += 1
                                continue

                            if not initial_date <= metadata_date <= final_date:
                                continue

                            article_files = ";".join(selected_article_locations[metadata.article_id])

                            writer.writerow(
                                [
                                    metadata.article_id,
                                    metadata.now_field_2,
                                    metadata.date_original,
                                    metadata.date_iso,
                                    metadata.country_code,
                                    metadata.source_name,
                                    metadata.url,
                                    metadata.title,
                                    article_files,
                                    relative_source_file,
                                ]
                            )

                            result.matched_ids.add(metadata.article_id)
                            result.metadata_match_counts[metadata.article_id] += 1
                            result.metadata_match_source_files[metadata.article_id].add(relative_source_file)
                            result.matched_metadata_rows += 1

                except OSError as exc:
                    result.unreadable_source_files += 1
                    logger.error("Failed to read source metadata file %s: %s", source_file, exc)

    except OSError as exc:
        logger.error("Failed to create main matched output file %s: %s", matched_sources_path, exc)
        raise

    logger.info("Source metadata lines scanned: %d", result.source_lines_scanned)
    logger.info("Matched metadata rows inside date range: %d", result.matched_metadata_rows)

    if result.malformed_metadata_lines:
        logger.warning("Malformed metadata lines skipped: %d", result.malformed_metadata_lines)

    if result.unreadable_source_files:
        logger.warning("Unreadable source metadata files: %d", result.unreadable_source_files)

    return result


def write_unmatched_article_ids(
    output_path: Path,
    selected_article_locations: dict[str, list[str]],
    matched_ids: set[str],
) -> int:
    unmatched_count = 0

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["article_id", "article_file"])

        for article_id in sorted(selected_article_locations):
            if article_id in matched_ids:
                continue

            writer.writerow([article_id, ";".join(selected_article_locations[article_id])])
            unmatched_count += 1

    return unmatched_count


def write_duplicate_article_ids(
    output_path: Path,
    selected_article_locations: dict[str, list[str]],
) -> int:
    duplicate_count = 0

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["article_id", "count", "article_files"])

        for article_id in sorted(selected_article_locations):
            locations = selected_article_locations[article_id]
            if len(locations) <= 1:
                continue

            writer.writerow([article_id, len(locations), ";".join(locations)])
            duplicate_count += 1

    return duplicate_count


def write_duplicate_metadata_matches(
    output_path: Path,
    metadata_match_counts: Counter[str],
    metadata_match_source_files: dict[str, set[str]],
    selected_article_locations: dict[str, list[str]],
) -> int:
    duplicate_count = 0

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["article_id", "match_count", "source_files", "article_files"])

        for article_id in sorted(metadata_match_counts):
            match_count = metadata_match_counts[article_id]
            if match_count <= 1:
                continue

            source_files = ";".join(sorted(metadata_match_source_files.get(article_id, set())))
            article_files = ";".join(selected_article_locations.get(article_id, []))
            writer.writerow([article_id, match_count, source_files, article_files])
            duplicate_count += 1

    return duplicate_count


def log_output_paths(match_dir: Path, logger: logging.Logger) -> None:
    logger.info("Matched sources output: %s", match_dir / MATCHED_SOURCES_FILENAME)
    logger.info("Unmatched article IDs output: %s", match_dir / UNMATCHED_ARTICLE_IDS_FILENAME)
    logger.info("Duplicate article IDs output: %s", match_dir / DUPLICATE_ARTICLE_IDS_FILENAME)
    logger.info("Duplicate metadata matches output: %s", match_dir / DUPLICATE_METADATA_MATCHES_FILENAME)
    logger.info("Log output: %s", match_dir / LOG_FILENAME)


def main() -> int:
    args = parse_args()

    try:
        initial_date = parse_iso_date(args.initial_date, "--initial-date")
        final_date = parse_iso_date(args.final_date, "--final-date")

        if initial_date > final_date:
            raise ValueError(
                f"--initial-date must not be later than --final-date: "
                f"{initial_date.isoformat()} > {final_date.isoformat()}"
            )

        input_sources = Path(args.input_sources).expanduser().resolve()
        input_articles = Path(args.input_articles).expanduser().resolve()
        match_dir = Path(args.match).expanduser().resolve()

        validate_input_directory(input_sources, "--input-sources")
        validate_input_directory(input_articles, "--input-articles")
        ensure_directory(match_dir)

    except (ValueError, FileNotFoundError, NotADirectoryError, OSError) as exc:
        print(f"ERROR {exc}")
        return 1

    logger = configure_logging(match_dir / LOG_FILENAME)

    logger.info("Starting NOW source/text matching")
    logger.info("Input sources directory: %s", input_sources)
    logger.info("Input articles directory: %s", input_articles)
    logger.info("Match output directory: %s", match_dir)
    logger.info("Initial date: %s", initial_date.isoformat())
    logger.info("Final date: %s", final_date.isoformat())

    matched_sources_path = match_dir / MATCHED_SOURCES_FILENAME
    unmatched_article_ids_path = match_dir / UNMATCHED_ARTICLE_IDS_FILENAME
    duplicate_article_ids_path = match_dir / DUPLICATE_ARTICLE_IDS_FILENAME
    duplicate_metadata_matches_path = match_dir / DUPLICATE_METADATA_MATCHES_FILENAME

    log_output_paths(match_dir, logger)

    try:
        article_result = collect_article_ids(input_articles, logger)

        metadata_result = scan_source_metadata(
            input_sources=input_sources,
            selected_article_locations=article_result.selected_article_locations,
            initial_date=initial_date,
            final_date=final_date,
            matched_sources_path=matched_sources_path,
            logger=logger,
        )

        unmatched_count = write_unmatched_article_ids(
            unmatched_article_ids_path,
            article_result.selected_article_locations,
            metadata_result.matched_ids,
        )

        duplicate_article_count = write_duplicate_article_ids(
            duplicate_article_ids_path,
            article_result.selected_article_locations,
        )

        duplicate_metadata_count = write_duplicate_metadata_matches(
            duplicate_metadata_matches_path,
            metadata_result.metadata_match_counts,
            metadata_result.metadata_match_source_files,
            article_result.selected_article_locations,
        )

    except OSError as exc:
        logger.error("Fatal output error: %s", exc)
        return 1

    logger.info("Selected article files found: %d", article_result.article_files_found)
    logger.info("Selected article lines scanned: %d", article_result.article_lines_scanned)
    logger.info("Selected article IDs found: %d", article_result.article_ids_found)
    logger.info("Unique selected article IDs: %d", len(article_result.selected_article_locations))
    logger.info("Duplicate selected article IDs written: %d", duplicate_article_count)
    logger.info("Malformed selected article lines: %d", article_result.malformed_article_lines)
    logger.info("Unreadable selected article files: %d", article_result.unreadable_article_files)

    logger.info("Source metadata files found: %d", metadata_result.source_files_found)
    logger.info("Source metadata lines scanned: %d", metadata_result.source_lines_scanned)
    logger.info("Matched metadata rows inside date range: %d", metadata_result.matched_metadata_rows)
    logger.info("Selected article IDs unmatched inside date range: %d", unmatched_count)
    logger.info("Duplicate metadata matches written: %d", duplicate_metadata_count)
    logger.info("Malformed metadata lines: %d", metadata_result.malformed_metadata_lines)
    logger.info("Unreadable source metadata files: %d", metadata_result.unreadable_source_files)

    logger.info("Processing complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())