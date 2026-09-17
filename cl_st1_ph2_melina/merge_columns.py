#!/usr/bin/env python3
"""
Merge clean binary keyword columns into one SAS/analysis-ready counts matrix.

Inputs:
    columns/000001.txt
        Reference full column file produced by columns.py.

        Expected format:
            file_id group presence

        Example:
            t000001 global_north_2023_09 1

    columns_clean/<Keyword ID>.txt
        Clean binary keyword-presence files produced by columns.py.

        Expected format:
            <Keyword ID>
            0
            1
            0
            ...

    file_ids.txt
        Mapping from generated file IDs to tagged corpus files.

        Expected format:
            file_id relative_tagged_path

        Example:
            t000001 global_north_2023_09/ca/101993957.txt

Output:
    sas/counts.txt

        Space-separated matrix with no header, suitable for SAS-style workflows.

        Output format:
            file_id group global_region year month country_code article_id kw000001 kw000002 ...

        Example:
            t000001 global_north_2023_09 north 2023 09 ca 101993957 0 1 0 ...
"""

import re
from pathlib import Path


# --- Configuration ---
CLEAN_DIR = Path("columns_clean")
COLUMNS_DIR = Path("columns")
FILE_IDS = Path("file_ids.txt")
OUTPUT_DIR = Path("sas")
OUTPUT_FILE = OUTPUT_DIR / "counts.txt"

GROUP_RE = re.compile(r"^global_(north|south)_(\d{4})_(\d{2})$")


def natural_sort_key(path):
    """Return a natural-sort key that treats digit runs as integers."""
    parts = re.split(r"(\d+)", str(path))
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def parse_group(group):
    """
    Parse a group label such as global_north_2023_09.

    Returns:
        tuple[str, str, str]: global_region, year, month
    """
    match = GROUP_RE.match(group)

    if not match:
        raise ValueError(
            f"Unexpected group format: {group!r}. "
            "Expected format such as global_north_2023_09 or global_south_2024_06."
        )

    global_region, year, month = match.groups()

    return global_region, year, month


def load_file_id_metadata(path):
    """
    Load file-id metadata from file_ids.txt.

    Expected file_ids.txt format:
        file_id relative_tagged_path

    Expected relative path format:
        group/country_code/article_id.txt

    Example:
        t000001 global_north_2023_09/ca/101993957.txt
    """
    if not path.exists():
        raise FileNotFoundError(f"File ID mapping not found: {path}")

    metadata = {}

    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            parts = line.split(maxsplit=1)

            if len(parts) != 2:
                raise ValueError(
                    f"Unexpected format in {path} at line {line_number}: "
                    "expected 'file_id relative_tagged_path'"
                )

            file_id, relative_path = parts
            path_parts = Path(relative_path).parts

            if len(path_parts) < 3:
                raise ValueError(
                    f"Unexpected tagged file path in {path} at line {line_number}: "
                    f"{relative_path!r}. Expected group/country_code/article_id.txt"
                )

            group = path_parts[0]
            country_code = path_parts[1]
            article_id = Path(path_parts[-1]).stem

            global_region, year, month = parse_group(group)

            metadata[file_id] = {
                "group": group,
                "global_region": global_region,
                "year": year,
                "month": month,
                "country_code": country_code,
                "article_id": article_id,
                "relative_path": relative_path,
            }

    if not metadata:
        raise ValueError(f"No file ID metadata loaded from {path}")

    return metadata


def load_reference_rows(path, file_metadata):
    """
    Load reference rows from columns/000001.txt.

    Expected format:
        file_id group presence

    The presence value is discarded; file_id and group are used for row ordering
    and cross-checking against file_ids.txt.
    """
    if not path.exists():
        raise FileNotFoundError(f"Reference file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        ref_lines = [line.strip().split() for line in f if line.strip()]

    if not ref_lines:
        raise ValueError(f"Reference file is empty: {path}")

    rows = []

    for line_number, cols in enumerate(ref_lines, start=1):
        if len(cols) != 3:
            raise ValueError(
                f"Unexpected format in {path} at line {line_number}: "
                f"expected 3 fields 'file_id group presence', found {len(cols)}"
            )

        file_id, group, presence = cols

        if presence not in {"0", "1"}:
            raise ValueError(
                f"Invalid binary presence flag in {path} at line {line_number}: {presence}"
            )

        if file_id not in file_metadata:
            raise ValueError(
                f"File ID {file_id!r} found in {path} at line {line_number}, "
                f"but it is missing from {FILE_IDS}"
            )

        metadata = file_metadata[file_id]

        if metadata["group"] != group:
            raise ValueError(
                f"Group mismatch for {file_id!r}: "
                f"{path} has {group!r}, but {FILE_IDS} has {metadata['group']!r}"
            )

        rows.append(
            [
                file_id,
                metadata["group"],
                metadata["global_region"],
                metadata["year"],
                metadata["month"],
                metadata["country_code"],
                metadata["article_id"],
            ]
        )

    return rows


def load_clean_column(path, expected_row_count):
    """
    Load a clean binary keyword column.

    Expected format:
        keyword_id
        binary_flag
        binary_flag
        ...

    Returns:
        tuple[str, list[str]]: keyword_id, flags
    """
    expected_keyword_id = path.stem

    with path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        raise ValueError(f"Clean column file is empty: {path}")

    keyword_id = lines[0]

    if keyword_id != expected_keyword_id:
        raise ValueError(
            f"Keyword ID mismatch in {path.name}: "
            f"first line is {keyword_id!r}, expected {expected_keyword_id!r}"
        )

    flags = lines[1:]

    if len(flags) != expected_row_count:
        raise ValueError(
            f"Row count mismatch in {path.name}: "
            f"{len(flags)} flags vs {expected_row_count} reference rows"
        )

    for row_number, flag in enumerate(flags, start=1):
        if flag not in {"0", "1"}:
            raise ValueError(
                f"Invalid binary flag in {path.name} at data row {row_number}: {flag!r}"
            )

    return keyword_id, flags


def main():
    # Ensure output directory exists.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Load file ID metadata.
    file_metadata = load_file_id_metadata(FILE_IDS)

    # Step 2: Read reference columns file to get row ordering and metadata.
    ref_file = COLUMNS_DIR / "000001.txt"
    output_rows = load_reference_rows(ref_file, file_metadata)

    # Step 3: Get sorted list of all clean column files.
    clean_files = sorted(CLEAN_DIR.glob("*.txt"), key=natural_sort_key)

    if not clean_files:
        raise FileNotFoundError(f"No clean column files found in {CLEAN_DIR}")

    # Step 4: Read each clean file and append its binary flags to output_rows.
    for clean_file in clean_files:
        keyword_id, flags = load_clean_column(
            clean_file,
            expected_row_count=len(output_rows),
        )

        for i, flag in enumerate(flags):
            output_rows[i].append(flag)

    # Step 5: Write merged data to sas/counts.txt.
    #
    # Output format:
    #   file_id group global_region year month country_code article_id kw000001 kw000002 ...
    #
    # No header; space-separated.
    with OUTPUT_FILE.open("w", encoding="utf-8") as out:
        for row in output_rows:
            out.write(" ".join(row) + "\n")

    print(f"Merged data written to {OUTPUT_FILE}")
    print(f"Rows written: {len(output_rows)}")
    print(f"Keyword columns merged: {len(clean_files)}")
    print("Output metadata columns:")
    print("→ file_id")
    print("→ group")
    print("→ global_region")
    print("→ year")
    print("→ month")
    print("→ country_code")
    print("→ article_id")
    print("→ keyword flags")


if __name__ == "__main__":
    main()