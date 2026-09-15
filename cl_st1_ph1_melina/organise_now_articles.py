#!/usr/bin/env python3
"""
organise_now_articles.py

Reorganise selected NOW corpus article lines into individual article files,
grouped by Global North/South classification, year-month of origin, and
country code.

The programme scans selected NOW article files inside month subdirectories,
extracts article IDs and article content from lines beginning with '@@',
writes only the first occurrence of each article ID, and produces diagnostic
files for duplicate IDs, malformed article lines, malformed filenames, and
unknown country codes.

Usage:
    python organise_now_articles.py \
        --initial-date 2023-09-01 \
        --final-date 2026-09-15 \
        --global-north-south-classification docs/now_country_codes_north_south.md \
        --input-articles corpus/01_now_dataset/02_now_text \
        --output-articles corpus/02_now_organised
"""

from __future__ import annotations

import argparse
import csv
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


DUPLICATE_ARTICLE_IDS_FILENAME = "duplicate_article_ids.tsv"
MALFORMED_SELECTED_ARTICLE_LINES_FILENAME = "malformed_selected_article_lines.tsv"
UNKNOWN_COUNTRY_CODES_FILENAME = "unknown_country_codes.tsv"
MALFORMED_ARTICLE_FILENAMES_FILENAME = "malformed_article_filenames.tsv"
LOG_FILENAME = "organise_now_articles.log"

ARTICLE_LINE_PATTERN = re.compile(r"^\s*@@(\d+)\b\s*(.*)$")
ARTICLE_FILENAME_PATTERN = re.compile(r"^\d{2}-\d{2}-([a-z]{2})(?:\d+)?\.txt$")
MONTH_DIR_PATTERN_SUFFIX = re.compile(r"^(\d{2})-(\d{2})-text$")
MONTH_DIR_PATTERN_PREFIX = re.compile(r"^text-(\d{2})-(\d{2})$")

MALFORMED_ARTICLE_FILENAME_REASON = "Filename does not match expected NOW article filename pattern"
UNKNOWN_COUNTRY_CODE_REASON = "Country code not found in Global North/South classification"


@dataclass(frozen=True)
class ArticleOccurrence:
    article_id: str
    article_file: str
    line_number: int
    year: int
    month: int
    country_code: str

    @property
    def year_month(self) -> str:
        return format_year_month(self.year, self.month)

    def to_descriptor(self) -> str:
        return f"{self.article_file}:{self.line_number}:{self.year_month}:{self.country_code}"


@dataclass(frozen=True)
class MalformedArticleLineRecord:
    article_file: str
    line_number: int
    year_month: str
    country_code: str
    line_preview: str


@dataclass(frozen=True)
class UnknownCountryCodeRecord:
    article_file: str
    year_month: str
    country_code: str
    reason: str


@dataclass(frozen=True)
class MalformedArticleFilenameRecord:
    article_file: str
    year_month: str
    reason: str


@dataclass
class MonthDirectorySelectionResult:
    selected_month_directories: list[tuple[Path, int, int]] = field(default_factory=list)
    ignored_unsupported_directories: int = 0
    ignored_out_of_range_directories: int = 0


@dataclass
class ProcessingResult:
    article_files_found: int = 0
    article_files_processed: int = 0
    article_files_skipped_malformed_filename: int = 0
    article_files_skipped_unknown_country_code: int = 0
    selected_article_lines_scanned: int = 0
    valid_article_lines_found: int = 0
    output_article_files_written: int = 0
    duplicate_article_occurrences_skipped: int = 0
    malformed_selected_article_lines_found: int = 0
    unreadable_article_files: int = 0
    seen_article_ids: set[str] = field(default_factory=set)
    article_occurrences: dict[str, list[ArticleOccurrence]] = field(default_factory=dict)
    malformed_selected_article_line_records: list[MalformedArticleLineRecord] = field(default_factory=list)
    unknown_country_code_records: list[UnknownCountryCodeRecord] = field(default_factory=list)
    malformed_article_filename_records: list[MalformedArticleFilenameRecord] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Organise selected NOW corpus article lines into individual files "
            "grouped by Global North/South classification, year-month, and country code."
        )
    )
    parser.add_argument(
        "--initial-date",
        required=True,
        help="First date to include, in ISO format: YYYY-MM-DD. Day is ignored for month selection.",
    )
    parser.add_argument(
        "--final-date",
        required=True,
        help="Final date to include, in ISO format: YYYY-MM-DD. Day is ignored for month selection.",
    )
    parser.add_argument(
        "--global-north-south-classification",
        required=True,
        help="Markdown file containing NOW country code and Global North/South mapping.",
    )
    parser.add_argument(
        "--input-articles",
        required=True,
        help="Directory containing selected NOW article text files.",
    )
    parser.add_argument(
        "--output-articles",
        required=True,
        help="Output directory where organised article files and diagnostics are written.",
    )
    return parser.parse_args()


def configure_logging(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("organise_now_articles")
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
    if not path.is_dir():
        raise NotADirectoryError(f"Output path exists but is not a directory: {path}")


def parse_iso_date(value: str, argument_name: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{argument_name} must be a valid ISO date in YYYY-MM-DD format: {value}") from exc


def date_to_year_month(value: date) -> tuple[int, int]:
    return value.year, value.month


def validate_input_directory(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"{label} is not a directory: {path}")


def validate_input_file(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"{label} is not a file: {path}")


def relative_posix_path(path: Path, base_dir: Path) -> str:
    return path.relative_to(base_dir).as_posix()


def format_year_month(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def format_year_month_for_directory(year: int, month: int) -> str:
    return f"{year:04d}_{month:02d}"


def parse_month_subdirectory_name(directory_name: str) -> tuple[int, int] | None:
    match = MONTH_DIR_PATTERN_SUFFIX.match(directory_name)
    if match is None:
        match = MONTH_DIR_PATTERN_PREFIX.match(directory_name)

    if match is None:
        return None

    year_text, month_text = match.groups()
    year = 2000 + int(year_text)
    month = int(month_text)

    if not 1 <= month <= 12:
        return None

    return year, month


def is_year_month_in_range(
    year: int,
    month: int,
    initial_year_month: tuple[int, int],
    final_year_month: tuple[int, int],
) -> bool:
    current = (year, month)
    return initial_year_month <= current <= final_year_month


def find_selected_month_directories(
    input_articles: Path,
    initial_year_month: tuple[int, int],
    final_year_month: tuple[int, int],
    logger: logging.Logger,
) -> MonthDirectorySelectionResult:
    result = MonthDirectorySelectionResult()

    directories = sorted(path for path in input_articles.rglob("*") if path.is_dir())

    for directory in directories:
        parsed_year_month = parse_month_subdirectory_name(directory.name)

        if parsed_year_month is None:
            result.ignored_unsupported_directories += 1
            continue

        year, month = parsed_year_month

        if not is_year_month_in_range(year, month, initial_year_month, final_year_month):
            result.ignored_out_of_range_directories += 1
            continue

        result.selected_month_directories.append((directory, year, month))

    logger.info("Selected month subdirectories found: %d", len(result.selected_month_directories))
    for directory, year, month in result.selected_month_directories:
        logger.info(
            "Selected month subdirectory: %s (%s)",
            relative_posix_path(directory, input_articles),
            format_year_month(year, month),
        )

    return result


def extract_country_code_from_filename(filename: str) -> str | None:
    match = ARTICLE_FILENAME_PATTERN.match(filename.lower())
    if match is None:
        return None
    return match.group(1).lower()


def parse_markdown_table_cells(line: str) -> list[str] | None:
    stripped = line.strip()

    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None

    cells = [cell.strip() for cell in stripped.strip("|").split("|")]

    if not cells:
        return None

    return cells


def is_markdown_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) is not None for cell in cells)


def load_global_classification(classification_path: Path) -> dict[str, str]:
    code_index: int | None = None
    global_index: int | None = None
    mapping: dict[str, str] = {}

    try:
        with classification_path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            for line in handle:
                cells = parse_markdown_table_cells(line)
                if cells is None:
                    continue

                if is_markdown_separator_row(cells):
                    continue

                normalized_cells = [cell.strip().lower() for cell in cells]

                if code_index is None or global_index is None:
                    if "code" in normalized_cells and "global" in normalized_cells:
                        code_index = normalized_cells.index("code")
                        global_index = normalized_cells.index("global")
                    continue

                if len(cells) <= max(code_index, global_index):
                    continue

                country_code = cells[code_index].strip().lower()
                global_region = cells[global_index].strip().lower()

                if not country_code or global_region not in {"north", "south"}:
                    continue

                mapping[country_code] = global_region

    except OSError as exc:
        raise OSError(f"Failed to read Global North/South classification file {classification_path}: {exc}") from exc

    if not mapping:
        raise ValueError(
            "Global North/South classification file could not be parsed or contains no valid records."
        )

    return mapping


def extract_article_from_line(line: str) -> tuple[str, str] | None:
    match = ARTICLE_LINE_PATTERN.match(line)
    if match is None:
        return None

    article_id = match.group(1)
    article_content = match.group(2).strip()
    return article_id, article_content


def make_line_preview(line: str, max_length: int = 250) -> str:
    normalized = line.replace("\t", " ").strip()
    if len(normalized) <= max_length:
        return normalized
    return normalized[:max_length] + "..."


def make_output_article_path(
    output_articles: Path,
    global_region: str,
    year: int,
    month: int,
    country_code: str,
    article_id: str,
) -> Path:
    if global_region not in {"north", "south"}:
        raise ValueError(f"Unexpected global region: {global_region}")

    directory_name = f"global_{global_region}_{format_year_month_for_directory(year, month)}"
    return output_articles / directory_name / country_code / f"{article_id}.txt"


def write_article_file(output_path: Path, article_content: str) -> None:
    if output_path.exists() and output_path.is_dir():
        raise IsADirectoryError(f"Cannot write article file because a directory exists at: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(article_content)
        handle.write("\n")


def process_article_file(
    article_file: Path,
    input_articles: Path,
    output_articles: Path,
    year: int,
    month: int,
    country_code: str,
    global_region: str,
    result: ProcessingResult,
    logger: logging.Logger,
) -> None:
    relative_article_file = relative_posix_path(article_file, input_articles)
    year_month = format_year_month(year, month)

    result.article_files_processed += 1

    try:
        with article_file.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.rstrip("\r\n")

                if not line:
                    continue

                result.selected_article_lines_scanned += 1

                extracted_article = extract_article_from_line(line)
                if extracted_article is None:
                    result.malformed_selected_article_lines_found += 1
                    result.malformed_selected_article_line_records.append(
                        MalformedArticleLineRecord(
                            article_file=relative_article_file,
                            line_number=line_number,
                            year_month=year_month,
                            country_code=country_code,
                            line_preview=make_line_preview(line),
                        )
                    )
                    continue

                article_id, article_content = extracted_article
                result.valid_article_lines_found += 1

                occurrence = ArticleOccurrence(
                    article_id=article_id,
                    article_file=relative_article_file,
                    line_number=line_number,
                    year=year,
                    month=month,
                    country_code=country_code,
                )
                result.article_occurrences.setdefault(article_id, []).append(occurrence)

                if article_id in result.seen_article_ids:
                    result.duplicate_article_occurrences_skipped += 1
                    continue

                result.seen_article_ids.add(article_id)

                output_path = make_output_article_path(
                    output_articles=output_articles,
                    global_region=global_region,
                    year=year,
                    month=month,
                    country_code=country_code,
                    article_id=article_id,
                )
                write_article_file(output_path, article_content)
                result.output_article_files_written += 1

    except OSError as exc:
        result.unreadable_article_files += 1
        logger.error("Failed to read or process selected article file %s: %s", article_file, exc)


def process_selected_month_directories(
    selected_month_directories: Iterable[tuple[Path, int, int]],
    input_articles: Path,
    output_articles: Path,
    country_code_to_global_region: dict[str, str],
    logger: logging.Logger,
) -> ProcessingResult:
    result = ProcessingResult()

    for month_directory, year, month in selected_month_directories:
        year_month = format_year_month(year, month)
        relative_month_directory = relative_posix_path(month_directory, input_articles)

        article_files = sorted(path for path in month_directory.rglob("*.txt") if path.is_file())
        result.article_files_found += len(article_files)

        logger.info(
            "Processing month subdirectory %s (%s): %d .txt file(s)",
            relative_month_directory,
            year_month,
            len(article_files),
        )

        for article_file in article_files:
            relative_article_file = relative_posix_path(article_file, input_articles)
            country_code = extract_country_code_from_filename(article_file.name)

            if country_code is None:
                result.article_files_skipped_malformed_filename += 1
                result.malformed_article_filename_records.append(
                    MalformedArticleFilenameRecord(
                        article_file=relative_article_file,
                        year_month=year_month,
                        reason=MALFORMED_ARTICLE_FILENAME_REASON,
                    )
                )
                continue

            global_region = country_code_to_global_region.get(country_code)
            if global_region is None:
                result.article_files_skipped_unknown_country_code += 1
                result.unknown_country_code_records.append(
                    UnknownCountryCodeRecord(
                        article_file=relative_article_file,
                        year_month=year_month,
                        country_code=country_code,
                        reason=UNKNOWN_COUNTRY_CODE_REASON,
                    )
                )
                continue

            process_article_file(
                article_file=article_file,
                input_articles=input_articles,
                output_articles=output_articles,
                year=year,
                month=month,
                country_code=country_code,
                global_region=global_region,
                result=result,
                logger=logger,
            )

    return result


def write_duplicate_article_ids(
    output_path: Path,
    article_occurrences: dict[str, list[ArticleOccurrence]],
) -> int:
    duplicate_count = 0

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(
            [
                "article_id",
                "occurrence_count",
                "first_article_file",
                "first_line_number",
                "first_year_month",
                "first_country_code",
                "all_occurrences",
            ]
        )

        for article_id in sorted(article_occurrences):
            occurrences = article_occurrences[article_id]
            if len(occurrences) <= 1:
                continue

            first = occurrences[0]
            writer.writerow(
                [
                    article_id,
                    len(occurrences),
                    first.article_file,
                    first.line_number,
                    first.year_month,
                    first.country_code,
                    ";".join(occurrence.to_descriptor() for occurrence in occurrences),
                ]
            )
            duplicate_count += 1

    return duplicate_count


def write_malformed_selected_article_lines(
    output_path: Path,
    malformed_records: Iterable[MalformedArticleLineRecord],
) -> int:
    malformed_count = 0

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["article_file", "line_number", "year_month", "country_code", "line_preview"])

        for record in malformed_records:
            writer.writerow(
                [
                    record.article_file,
                    record.line_number,
                    record.year_month,
                    record.country_code,
                    record.line_preview,
                ]
            )
            malformed_count += 1

    return malformed_count


def write_unknown_country_codes(
    output_path: Path,
    unknown_country_code_records: Iterable[UnknownCountryCodeRecord],
) -> int:
    unknown_country_code_count = 0

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["article_file", "year_month", "country_code", "reason"])

        for record in unknown_country_code_records:
            writer.writerow([record.article_file, record.year_month, record.country_code, record.reason])
            unknown_country_code_count += 1

    return unknown_country_code_count


def write_malformed_article_filenames(
    output_path: Path,
    malformed_article_filename_records: Iterable[MalformedArticleFilenameRecord],
) -> int:
    malformed_filename_count = 0

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["article_file", "year_month", "reason"])

        for record in malformed_article_filename_records:
            writer.writerow([record.article_file, record.year_month, record.reason])
            malformed_filename_count += 1

    return malformed_filename_count


def log_output_paths(output_articles: Path, logger: logging.Logger) -> None:
    logger.info("Duplicate article IDs output: %s", output_articles / DUPLICATE_ARTICLE_IDS_FILENAME)
    logger.info(
        "Malformed selected article lines output: %s",
        output_articles / MALFORMED_SELECTED_ARTICLE_LINES_FILENAME,
    )
    logger.info("Unknown country codes output: %s", output_articles / UNKNOWN_COUNTRY_CODES_FILENAME)
    logger.info("Malformed article filenames output: %s", output_articles / MALFORMED_ARTICLE_FILENAMES_FILENAME)
    logger.info("Log output: %s", output_articles / LOG_FILENAME)


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

        classification_file = Path(args.global_north_south_classification).expanduser().resolve()
        input_articles = Path(args.input_articles).expanduser().resolve()
        output_articles = Path(args.output_articles).expanduser().resolve()

        validate_input_file(classification_file, "--global-north-south-classification")
        validate_input_directory(input_articles, "--input-articles")
        ensure_directory(output_articles)

        country_code_to_global_region = load_global_classification(classification_file)

    except (ValueError, FileNotFoundError, NotADirectoryError, OSError) as exc:
        print(f"ERROR {exc}")
        return 1

    logger = configure_logging(output_articles / LOG_FILENAME)

    initial_year_month = date_to_year_month(initial_date)
    final_year_month = date_to_year_month(final_date)

    logger.info("Starting NOW article organisation")
    logger.info("Input articles directory: %s", input_articles)
    logger.info("Output articles directory: %s", output_articles)
    logger.info("Global North/South classification file: %s", classification_file)
    logger.info("Initial date: %s", initial_date.isoformat())
    logger.info("Final date: %s", final_date.isoformat())
    logger.info("Initial year-month: %s", format_year_month(*initial_year_month))
    logger.info("Final year-month: %s", format_year_month(*final_year_month))
    logger.info("Classification records loaded: %d", len(country_code_to_global_region))

    log_output_paths(output_articles, logger)

    duplicate_article_ids_path = output_articles / DUPLICATE_ARTICLE_IDS_FILENAME
    malformed_selected_article_lines_path = output_articles / MALFORMED_SELECTED_ARTICLE_LINES_FILENAME
    unknown_country_codes_path = output_articles / UNKNOWN_COUNTRY_CODES_FILENAME
    malformed_article_filenames_path = output_articles / MALFORMED_ARTICLE_FILENAMES_FILENAME

    try:
        month_selection_result = find_selected_month_directories(
            input_articles=input_articles,
            initial_year_month=initial_year_month,
            final_year_month=final_year_month,
            logger=logger,
        )

        processing_result = process_selected_month_directories(
            selected_month_directories=month_selection_result.selected_month_directories,
            input_articles=input_articles,
            output_articles=output_articles,
            country_code_to_global_region=country_code_to_global_region,
            logger=logger,
        )

        duplicate_article_ids_written = write_duplicate_article_ids(
            duplicate_article_ids_path,
            processing_result.article_occurrences,
        )

        malformed_selected_article_lines_written = write_malformed_selected_article_lines(
            malformed_selected_article_lines_path,
            processing_result.malformed_selected_article_line_records,
        )

        unknown_country_code_records_written = write_unknown_country_codes(
            unknown_country_codes_path,
            processing_result.unknown_country_code_records,
        )

        malformed_article_filename_records_written = write_malformed_article_filenames(
            malformed_article_filenames_path,
            processing_result.malformed_article_filename_records,
        )

    except OSError as exc:
        logger.error("Fatal output error: %s", exc)
        return 1

    duplicate_article_ids_found = sum(
        1 for occurrences in processing_result.article_occurrences.values()
        if len(occurrences) > 1
    )

    logger.info("Selected month subdirectories processed: %d", len(month_selection_result.selected_month_directories))
    logger.info(
        "Ignored subdirectories because of unsupported naming format: %d",
        month_selection_result.ignored_unsupported_directories,
    )
    logger.info(
        "Ignored subdirectories outside requested year-month range: %d",
        month_selection_result.ignored_out_of_range_directories,
    )
    logger.info("Article files found in selected month subdirectories: %d", processing_result.article_files_found)
    logger.info("Article files processed: %d", processing_result.article_files_processed)
    logger.info(
        "Article files skipped because of malformed filenames: %d",
        processing_result.article_files_skipped_malformed_filename,
    )
    logger.info(
        "Article files skipped because of unknown country codes: %d",
        processing_result.article_files_skipped_unknown_country_code,
    )
    logger.info("Selected article lines scanned: %d", processing_result.selected_article_lines_scanned)
    logger.info("Valid article lines found: %d", processing_result.valid_article_lines_found)
    logger.info("Unique article IDs written: %d", len(processing_result.seen_article_ids))
    logger.info("Duplicate article IDs found: %d", duplicate_article_ids_found)
    logger.info("Duplicate article IDs written: %d", duplicate_article_ids_written)
    logger.info(
        "Duplicate article occurrences skipped: %d",
        processing_result.duplicate_article_occurrences_skipped,
    )
    logger.info(
        "Malformed selected article lines found: %d",
        processing_result.malformed_selected_article_lines_found,
    )
    logger.info(
        "Malformed selected article lines written: %d",
        malformed_selected_article_lines_written,
    )
    logger.info("Unknown country code records written: %d", unknown_country_code_records_written)
    logger.info("Malformed article filename records written: %d", malformed_article_filename_records_written)
    logger.info("Unreadable article files: %d", processing_result.unreadable_article_files)
    logger.info("Output article files written: %d", processing_result.output_article_files_written)
    logger.info("Processing complete")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())