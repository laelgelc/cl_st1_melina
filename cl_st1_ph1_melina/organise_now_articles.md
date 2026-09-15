# Development Specification: `organise_now_articles.py`

## 1. Purpose

`organise_now_articles.py` is a Python programme for reorganising selected NOW corpus article lines into individual article files, grouped by:

1. Global North/South classification;
2. year and month of origin;
3. country code.

The programme processes selected NOW article text files that contain one article per line. Each valid article line begins with an article ID introduced by `@@`, followed by the article content.

Example selected article line:

```plain text
@@101631126 <p> GAZA , - Israel will allow the export of commercial goods from the Gaza Strip through a main border crossing from Sunday after a days-long ban for
```

The programme will:

1. Parse `--initial-date` and `--final-date`.
2. Convert the requested date range into an inclusive year-month range.
3. Recursively inspect the first-level or nested subdirectories under `--input-articles`.
4. Select only subdirectories whose names encode a year and month inside the requested year-month range.
5. Parse NOW article `.txt` files inside those selected subdirectories.
6. Extract country codes from article filenames.
7. Load the Global North/South classification from the Markdown table specified by `--global-north-south-classification`.
8. Extract article IDs and article content from selected article lines.
9. Detect duplicate article IDs across all selected subdirectories and files.
10. Write only the first valid occurrence of each article ID.
11. Report duplicate article IDs in a diagnostic file.
12. Report malformed selected article lines in a diagnostic file.
13. Report unknown or unclassified country codes in a diagnostic file.
14. Write each article as a separate `.txt` file named after its article ID.
15. Organise output files under `--output-articles` using the structure:

```plain text
global_north_YYYY_MM/<country_code>/<article_id>.txt
global_south_YYYY_MM/<country_code>/<article_id>.txt
```

Example output structure:

```plain text
corpus/
├── 02_now_organised/
    ├── global_north_2023_09/
    │   ├── au/
    │   │   ├── 101631127.txt
    │   │   └── 101631128.txt
    │   ├── ca/
    │   │   ├── 101631129.txt
    │   │   ├── 101631130.txt
    │   │   └── 101631131.txt
    │
    ├── global_south_2023_09/
    │   ├── bd/
    │   │   ├── 101631127.txt
    │   │   └── 101631128.txt
    │   ├── gh/
    │   │   ├── 101631129.txt
    │   │   ├── 101631130.txt
    │   │   └── 101631131.txt
```

---

## 2. Command-line Interface

The programme must be executable from the command line as follows:

```shell
python organise_now_articles.py \
    --initial-date 2023-09-01 \
    --final-date 2026-09-15 \
    --global-north-south-classification docs/now_country_codes_north_south.md \
    --input-articles corpus/01_now_dataset/02_now_text \
    --output-articles corpus/02_now_organised
```

## 2.1 Required arguments

| Argument                              | Required | Description                                                                 |
|---------------------------------------|---------:|-----------------------------------------------------------------------------|
| `--initial-date`                      | Yes      | First date to include, in ISO format: `YYYY-MM-DD`.                         |
| `--final-date`                        | Yes      | Final date to include, in ISO format: `YYYY-MM-DD`.                         |
| `--global-north-south-classification` | Yes      | Markdown file containing NOW country code and Global North/South mapping.    |
| `--input-articles`                    | Yes      | Directory containing selected NOW article text files.                       |
| `--output-articles`                   | Yes      | Output directory where organised article files and diagnostics are written. |

---

## 2.2 Date range semantics

The programme must interpret the CLI date range at **year-month granularity**, because the input subdirectories encode only year and month.

For example:

```shell
--initial-date 2023-09-01 --final-date 2026-09-15
```

must be interpreted as the inclusive year-month range:

```plain text
2023-09 through 2026-09
```

The day component of the CLI dates must be parsed and validated, but ignored when selecting input subdirectories.

Therefore:

```shell
--initial-date 2023-09-30 --final-date 2023-10-01
```

must include subdirectories for:

```plain text
2023-09
2023-10
```

not only articles between the two specific days.

---

## 2.3 Invalid argument handling

The programme must terminate with a non-zero exit code if:

- `--initial-date` is not a valid ISO date;
- `--final-date` is not a valid ISO date;
- `--initial-date` is later than `--final-date`;
- `--global-north-south-classification` does not exist;
- `--global-north-south-classification` is not a file;
- `--input-articles` does not exist;
- `--input-articles` is not a directory;
- `--output-articles` cannot be created;
- `--output-articles` exists but is not a directory;
- the Global North/South classification file cannot be parsed.

The `--output-articles` directory must be created if it does not exist.

---

## 3. Input Data

## 3.1 Input article directory

The programme must process selected article text files under:

```plain text
--input-articles
```

Example:

```plain text
corpus/01_now_dataset/02_now_text
```

The input directory contains month subdirectories. Relevant subdirectories may be named in either of the following formats:

```plain text
23-09-text
23-10-text
text-25-01
text-25-02
```

Both naming styles encode year and month.

---

## 3.2 Month subdirectory format

The programme must detect year and month from subdirectory names using these supported conceptual patterns:

```plain text
^(\d{2})-(\d{2})-text$
^text-(\d{2})-(\d{2})$
```

Examples:

| Subdirectory name | Year | Month | ISO year-month |
|-------------------|------|-------|----------------|
| `23-09-text`      | 2023 | 09    | `2023-09`      |
| `23-10-text`      | 2023 | 10    | `2023-10`      |
| `text-25-01`      | 2025 | 01    | `2025-01`      |
| `text-25-02`      | 2025 | 02    | `2025-02`      |

The two-digit year must be interpreted as 2000-based:

```plain text
23 -> 2023
25 -> 2025
26 -> 2026
```

Subdirectories that do not match a supported month-directory pattern must be ignored.

---

## 3.3 Month subdirectory selection

The programme must select only month subdirectories whose inferred year-month falls inside the inclusive year-month range derived from `--initial-date` and `--final-date`.

Example:

```shell
--initial-date 2023-09-01
--final-date 2026-09-15
```

Selected year-months include:

```plain text
2023-09
2023-10
...
2026-08
2026-09
```

If `--input-articles` contains:

```plain text
23-08-text
23-09-text
23-10-text
text-25-01
text-25-02
```

then `23-08-text` must be skipped, while the others must be included if they fall inside the requested range.

---

## 3.4 Selected article files

Inside each selected month subdirectory, the programme must recursively process `.txt` files.

Article filenames are expected to contain:

1. a two-digit year;
2. a two-digit month;
3. a country code;
4. optional numeric suffixes for split files.

Examples:

```plain text
23-09-gb.txt
23-09-ph.txt
21-07-us1.txt
21-07-us2.txt
22-06-ca.txt
```

---

## 3.5 Country code extraction from filenames

The country code must be extracted from the selected article filename.

The conceptual filename pattern is:

```plain text
^\d{2}-\d{2}-([a-z]{2})(?:\d+)?\.txt$
```

This means:

- `23-09-gb.txt` captures `gb`;
- `23-09-ph.txt` captures `ph`;
- `21-07-us1.txt` captures `us`;
- `21-07-us2.txt` captures `us`;
- `22-06-ca.txt` captures `ca`.

Country codes must be normalised to lowercase before classification and output directory creation.

Files whose names do not contain a valid country code must be skipped and reported in a diagnostic file.

---

## 3.6 Selected article line format

Each selected article file is expected to contain one article per line.

Valid selected article lines begin with an article ID introduced by `@@`.

Example:

```plain text
@@101631126 <p> GAZA , - Israel will allow the export of commercial goods from the Gaza Strip through a main border crossing from Sunday after a days-long ban for
```

The article ID must be extracted from the beginning of the line using the following conceptual pattern:

```plain text
^\s*@@(\d+)\b
```

The article content is everything after the matched article ID marker.

For example:

```plain text
@@101631126 <p> GAZA , - Israel will allow...
```

must produce:

| Field             | Value                               |
|-------------------|-------------------------------------|
| `article_id`      | `101631126`                         |
| `article_content` | `<p> GAZA , - Israel will allow...` |

The leading whitespace between the article ID and the article content should be stripped from the output article content.

---

## 3.7 Malformed selected article lines

A non-empty line in a selected article file must be treated as malformed if it does not begin with a valid `@@` article ID.

Malformed selected article lines must be:

- counted;
- skipped;
- written to a diagnostic file.

Malformed lines must not stop the programme.

---

## 4. Global North/South Classification

## 4.1 Classification file

The programme must load country classifications from the Markdown file specified by:

```plain text
--global-north-south-classification
```

The file is expected to contain a Markdown table with at least these columns:

```plain text
Code
Global
```

Example:

```markdown
| Code | Country                        | Global |
|:-----|:-------------------------------|:-------|
| au   | Australia                      | North  |
| bd   | Bangladesh                     | South  |
| ca   | Canada                         | North  |
| gb   | Great Britain (United Kingdom) | North  |
| ph   | Philippines                    | South  |
| us   | United States                  | North  |
```

---

## 4.2 Classification parsing

The programme must parse the Markdown table and build an in-memory mapping:

```python
country_code_to_global_region: dict[str, str]
```

Example conceptual mapping:

```python
{
    "au": "north",
    "bd": "south",
    "ca": "north",
    "gb": "north",
    "ph": "south",
    "us": "north",
}
```

The parser should:

- ignore non-table lines;
- ignore Markdown separator rows such as `|:-----|:-------|`;
- strip whitespace around table cell values;
- normalise country codes to lowercase;
- normalise global classification values to lowercase.

Accepted global classification values:

```plain text
North
South
north
south
```

Classification values must be converted into output directory prefixes:

| Classification value | Output directory prefix |
|----------------------|-------------------------|
| `North`              | `global_north`          |
| `South`              | `global_south`          |

---

## 4.3 Unknown or unclassified country codes

If an article file has a valid country code in its filename but that country code does not appear in the classification mapping, then the programme must:

- skip all valid article lines from that file;
- count the file or affected article lines as unclassified;
- write a diagnostic record to an unknown-country-code diagnostic file;
- continue processing.

The first implementation should not infer or guess classifications.

---

## 5. Duplicate Article ID Handling

## 5.1 Duplicate definition

A duplicate article ID is any article ID that appears more than once across all selected article files in the selected month subdirectories.

Duplicates may occur:

- within the same file;
- across multiple files in the same month subdirectory;
- across different month subdirectories;
- across different country-code files.

---

## 5.2 Duplicate processing rule

Only the **first valid occurrence** of an article ID must be written to the organised output.

All later occurrences of the same article ID must be:

- counted as duplicates;
- skipped;
- reported in `duplicate_article_ids.tsv`.

The first occurrence is determined by deterministic traversal order:

1. selected month subdirectories sorted by relative path;
2. article files sorted by relative path;
3. line number within each file.

This deterministic ordering is required so repeated runs produce the same output.

---

## 5.3 Duplicate diagnostic requirements

The duplicate diagnostic file must record:

- the article ID;
- the total number of valid occurrences;
- the first occurrence location;
- all occurrence locations.

Each occurrence location should include:

- month subdirectory;
- article file path relative to `--input-articles`;
- line number;
- inferred year-month;
- country code.

---

## 6. Output Organisation

## 6.1 Output article directory

The `--output-articles` argument must be treated as the root output directory.

Example:

```plain text
corpus/02_now_organised
```

The programme must create this directory if it does not exist.

---

## 6.2 Output directory naming

Each valid, non-duplicate article must be written under:

```plain text
<output-articles>/<global_region>_<YYYY>_<MM>/<country_code>/<article_id>.txt
```

Where:

| Component       | Source                                  |
|-----------------|-----------------------------------------|
| `global_region` | Global North/South classification file  |
| `YYYY`          | Inferred from origin year subdirectory  |
| `MM`            | Inferred from origin month subdirectory |
| `country_code`  | Extracted from article filename         |
| `article_id`    | Extracted from article line             |

Examples:

```plain text
corpus/02_now_organised/global_north_2023_09/gb/101631126.txt
corpus/02_now_organised/global_south_2023_09/ph/101631127.txt
corpus/02_now_organised/global_north_2025_02/us/101631128.txt
```

---

## 6.3 Output file content

Each output `.txt` file must contain only the article content, not the `@@` article ID marker.

Input line:

```plain text
@@101631126 <p> GAZA , - Israel will allow the export of commercial goods from the Gaza Strip...
```

Output file:

```plain text
<p> GAZA , - Israel will allow the export of commercial goods from the Gaza Strip...
```

The output article file should end with a single LF newline.

---

## 6.4 Output file overwrite behaviour

Because only the first occurrence of each article ID is written, the programme should not normally attempt to write the same article ID twice.

If the target output file already exists from a previous run, the recommended first-version behaviour is:

- overwrite the existing file;
- log that the output directory may contain files from a previous run.

Optional later enhancement:

- add `--clean-output` to remove existing output before writing.

The first version does not require `--clean-output`.

---

## 7. Diagnostic Output Files

The programme must write diagnostic files inside the `--output-articles` directory.

Required diagnostic files:

```plain text
duplicate_article_ids.tsv
malformed_selected_article_lines.tsv
unknown_country_codes.tsv
malformed_article_filenames.tsv
organise_now_articles.log
```

All diagnostic files must be created even if they contain only a header row.

---

## 7.1 `duplicate_article_ids.tsv`

This diagnostic file must contain article IDs that occur more than once among valid selected article lines.

### 7.1.1 Required columns

```plain text
article_id
occurrence_count
first_article_file
first_line_number
first_year_month
first_country_code
all_occurrences
```

Recommended header:

```plain text
article_id	occurrence_count	first_article_file	first_line_number	first_year_month	first_country_code	all_occurrences
```

### 7.1.2 `all_occurrences` format

The `all_occurrences` field should contain a semicolon-separated list of occurrence descriptors.

Recommended descriptor format:

```plain text
article_file:line_number:year_month:country_code
```

Example:

```plain text
23-09-text/23-09-gb.txt:12:2023-09:gb;23-09-text/23-09-ph.txt:42:2023-09:ph
```

---

## 7.2 `malformed_selected_article_lines.tsv`

This diagnostic file must contain non-empty selected article lines that could not be parsed as valid article lines.

### 7.2.1 Required columns

```plain text
article_file
line_number
year_month
country_code
line_preview
```

Recommended header:

```plain text
article_file	line_number	year_month	country_code	line_preview
```

Where:

- `article_file` is the selected article file path relative to `--input-articles`;
- `line_number` is the 1-based line number in the selected article file;
- `year_month` is inferred from the origin month subdirectory;
- `country_code` is extracted from the filename if available;
- `line_preview` is a short, tab-safe preview of the malformed line.

### 7.2.2 Line preview handling

The line preview should:

- strip leading and trailing whitespace;
- replace tab characters with spaces;
- be truncated to a reasonable maximum length, e.g. 250 characters.

---

## 7.3 `unknown_country_codes.tsv`

This diagnostic file must contain article files whose country code was syntactically valid but missing from the Global North/South classification mapping.

### 7.3.1 Required columns

```plain text
article_file
year_month
country_code
reason
```

Recommended header:

```plain text
article_file	year_month	country_code	reason
```

Example row:

```plain text
23-09-text/23-09-xx.txt	2023-09	xx	Country code not found in Global North/South classification
```

---

## 7.4 `malformed_article_filenames.tsv`

This diagnostic file must contain `.txt` files in selected month subdirectories whose filenames do not contain a valid country code.

### 7.4.1 Required columns

```plain text
article_file
year_month
reason
```

Recommended header:

```plain text
article_file	year_month	reason
```

Example row:

```plain text
23-09-text/readme.txt	2023-09	Filename does not match expected NOW article filename pattern
```

---

## 7.5 `organise_now_articles.log`

The programme must write a log file named:

```plain text
organise_now_articles.log
```

The log file must be written inside the `--output-articles` directory.

The programme should also log to the console.

---

## 8. Logging Requirements

The programme must use standard logging levels:

- `INFO`
- `WARNING`
- `ERROR`

## 8.1 Required log information

The log must include:

- programme start;
- programme completion;
- resolved input and output paths;
- path to the Global North/South classification file;
- parsed initial date;
- parsed final date;
- derived initial year-month;
- derived final year-month;
- number of classification records loaded;
- selected month subdirectories found;
- selected month subdirectories processed;
- ignored subdirectories because of unsupported naming format;
- ignored subdirectories outside the requested year-month range;
- article files found in selected month subdirectories;
- article files processed;
- article files skipped because of malformed filenames;
- article files skipped because of unknown country codes;
- selected article lines scanned;
- valid article lines found;
- unique article IDs written;
- duplicate article IDs found;
- duplicate article occurrences skipped;
- malformed selected article lines found;
- malformed selected article lines written;
- unknown country code records written;
- malformed article filename records written;
- unreadable article files;
- output article files written;
- paths to all diagnostic files;
- path to the log file.

---

## 8.2 Logging volume

The programme must avoid logging every successfully written article line.

For large datasets, per-line logging would be too slow and would create excessively large log files.

The programme should log:

- high-level summaries;
- selected month subdirectory names;
- recoverable file-level errors;
- final processing counts.

---

## 9. Performance Requirements

The programme must be suitable for thousands of article files and potentially many article lines.

Therefore:

1. Input article files must be read line by line.
2. Full article files must not be loaded into memory.
3. Article IDs may be kept in memory to detect duplicates.
4. Duplicate diagnostic information may be kept in memory.
5. Output article files should be written as soon as a valid non-duplicate article line is processed.
6. The programme should skip files as early as possible if:
   - the filename is malformed;
   - the country code is unknown;
   - the origin month subdirectory is outside the requested range.

Recommended processing strategy:

```plain text
Load Global North/South classification.

Find selected month subdirectories.

For each selected month subdirectory:
    infer year-month from subdirectory name

    For each .txt file under that subdirectory:
        extract country code from filename
        if filename malformed:
            record malformed filename
            skip file

        lookup country code in classification
        if country code unknown:
            record unknown country code
            skip file

        For each non-empty line:
            parse article ID and article content
            if malformed:
                record malformed line
                continue

            record article ID occurrence
            if article ID has already been written:
                count duplicate occurrence
                continue

            create output directory
            write article content to:
                global_<north_or_south>_YYYY_MM/<country_code>/<article_id>.txt
```

---

## 10. Error Handling

## 10.1 Recoverable errors

The programme should continue after recoverable errors such as:

- unsupported subdirectory names;
- subdirectories outside the requested year-month range;
- malformed article filenames;
- unknown country codes;
- unreadable individual article files;
- malformed selected article lines;
- duplicate article IDs.

Recoverable errors must be logged or written to diagnostic files where applicable.

---

## 10.2 Fatal errors

The programme must terminate with a non-zero exit code for fatal errors such as:

- invalid CLI date format;
- `--initial-date` later than `--final-date`;
- missing input article directory;
- invalid input article directory;
- missing classification file;
- invalid classification file;
- inability to parse any valid classification records;
- inability to create the output directory;
- inability to write required diagnostic files;
- unexpected output path conflict where a directory exists where an article file must be written.

---

## 11. File Encoding and Line Endings

## 11.1 Input files

Input files should be opened with:

```plain text
UTF-8 encoding
errors="replace"
```

This prevents the programme from failing because of occasional invalid byte sequences.

---

## 11.2 Output files

Output files must be:

- UTF-8 encoded;
- written with LF line endings;
- tab-separated where applicable.

Each organised article `.txt` file should contain:

- article content only;
- no `@@` article ID prefix;
- one final newline.

---

## 12. Programme Structure

The implementation should be modular and readable.

Recommended functions:

| Function                                   | Responsibility                                                                  |
|--------------------------------------------|---------------------------------------------------------------------------------|
| `parse_args()`                             | Parse command-line arguments.                                                   |
| `configure_logging()`                      | Set up console and file logging.                                                |
| `ensure_directory()`                       | Create output directory if needed.                                              |
| `parse_iso_date()`                         | Parse CLI dates.                                                                |
| `date_to_year_month()`                     | Convert a date object to `(year, month)`.                                       |
| `validate_input_directory()`               | Validate that `--input-articles` exists and is a directory.                     |
| `validate_input_file()`                    | Validate that the classification file exists and is a file.                     |
| `relative_posix_path()`                    | Convert paths to relative POSIX-style paths for stable diagnostics.             |
| `parse_month_subdirectory_name()`          | Infer `(year, month)` from supported month subdirectory names.                  |
| `is_year_month_in_range()`                 | Check whether a subdirectory year-month is inside the requested range.          |
| `find_selected_month_directories()`        | Find and sort month subdirectories inside the requested year-month range.       |
| `extract_country_code_from_filename()`     | Extract country code from filenames such as `23-09-gb.txt` and `21-07-us1.txt`. |
| `load_global_classification()`             | Parse the Markdown table and build country code to global region mapping.       |
| `extract_article_from_line()`              | Extract article ID and article content from a selected article line.            |
| `make_line_preview()`                      | Produce a short, tab-safe preview of malformed selected article lines.          |
| `make_output_article_path()`               | Build the destination path for an article.                                      |
| `write_article_file()`                     | Write one article content file.                                                 |
| `process_article_file()`                   | Process one selected article file line by line.                                 |
| `process_selected_month_directories()`     | Coordinate article file processing for all selected month directories.          |
| `write_duplicate_article_ids()`            | Write duplicate article ID diagnostic file.                                     |
| `write_malformed_selected_article_lines()` | Write malformed selected article line diagnostic file.                          |
| `write_unknown_country_codes()`            | Write unknown country code diagnostic file.                                     |
| `write_malformed_article_filenames()`      | Write malformed article filename diagnostic file.                               |
| `log_output_paths()`                       | Log paths of all output and diagnostic files.                                   |
| `main()`                                   | Coordinate the complete programme.                                              |

---

## 13. Recommended Constants

Recommended filename constants:

```python
DUPLICATE_ARTICLE_IDS_FILENAME = "duplicate_article_ids.tsv"
MALFORMED_SELECTED_ARTICLE_LINES_FILENAME = "malformed_selected_article_lines.tsv"
UNKNOWN_COUNTRY_CODES_FILENAME = "unknown_country_codes.tsv"
MALFORMED_ARTICLE_FILENAMES_FILENAME = "malformed_article_filenames.tsv"
LOG_FILENAME = "organise_now_articles.log"
```

Recommended regular expression constants:

```python
ARTICLE_LINE_PATTERN = re.compile(r"^\s*@@(\d+)\b\s*(.*)$")
ARTICLE_FILENAME_PATTERN = re.compile(r"^\d{2}-\d{2}-([a-z]{2})(?:\d+)?\.txt$")
MONTH_DIR_PATTERN_SUFFIX = re.compile(r"^(\d{2})-(\d{2})-text$")
MONTH_DIR_PATTERN_PREFIX = re.compile(r"^text-(\d{2})-(\d{2})$")
```

---

## 14. Data Structures

Recommended data structures:

```python
country_code_to_global_region: dict[str, str]
```

Maps NOW country codes to normalised global regions:

```python
{
    "gb": "north",
    "ph": "south",
    "us": "north",
}
```

```python
seen_article_ids: set[str]
```

Tracks article IDs whose first occurrence has already been written.

```python
article_occurrences: dict[str, list[ArticleOccurrence]]
```

Tracks all valid occurrences of each article ID for duplicate diagnostics.

Recommended `ArticleOccurrence` fields:

```python
article_id: str
article_file: str
line_number: int
year: int
month: int
country_code: str
```

```python
malformed_selected_article_line_records: list[MalformedArticleLineRecord]
```

Stores malformed line diagnostics.

Recommended fields:

```python
article_file: str
line_number: int
year_month: str
country_code: str
line_preview: str
```

```python
unknown_country_code_records: list[UnknownCountryCodeRecord]
```

Stores valid but unclassified country code diagnostics.

Recommended fields:

```python
article_file: str
year_month: str
country_code: str
reason: str
```

```python
malformed_article_filename_records: list[MalformedArticleFilenameRecord]
```

Stores malformed filename diagnostics.

Recommended fields:

```python
article_file: str
year_month: str
reason: str
```

A dataclass-based implementation is recommended for readability.

---

## 15. Expected Processing Logic

## 15.1 High-level pseudocode

```plain text
Parse command-line arguments.

Resolve paths.

Validate:
    initial date
    final date
    classification file
    input article directory

Create output article directory.

Configure logging.

Define diagnostic output paths:
    duplicate_article_ids.tsv
    malformed_selected_article_lines.tsv
    unknown_country_codes.tsv
    malformed_article_filenames.tsv
    organise_now_articles.log

Load Global North/South classification:
    parse Markdown table
    build country_code_to_global_region mapping
    fail if no valid classification records are loaded

Convert initial and final dates to year-month values:
    initial_year_month
    final_year_month

Find selected month subdirectories:
    recursively inspect directories under input articles
    parse supported month directory names
    ignore unsupported names
    include only directories inside inclusive year-month range
    sort selected directories deterministically

For each selected month directory:
    infer origin year and month

    Find .txt files recursively inside it.
    Sort article files deterministically.

    For each article file:
        extract country code from filename

        if filename is malformed:
            record malformed article filename
            continue

        normalise country code to lowercase

        if country code is missing from classification mapping:
            record unknown country code
            continue

        determine global output prefix:
            North -> global_north
            South -> global_south

        Open article file with UTF-8 and errors="replace".

        For each line with 1-based line number:
            skip blank lines

            extract article ID and article content

            if line is malformed:
                record malformed selected article line
                continue

            record this valid article occurrence

            if article ID already exists in seen_article_ids:
                count duplicate skipped occurrence
                continue

            add article ID to seen_article_ids

            build output path:
                output_articles/global_<north_or_south>_YYYY_MM/country_code/article_id.txt

            create output parent directory

            write article content to output file

After processing:
    write duplicate_article_ids.tsv
    write malformed_selected_article_lines.tsv
    write unknown_country_codes.tsv
    write malformed_article_filenames.tsv

Log summary.

Exit with code 0 if successful.
```

---

## 16. Output Examples

## 16.1 Input example

Input file:

```plain text
corpus/01_now_dataset/02_now_text/23-09-text/23-09-gb.txt
```

Input line:

```plain text
@@101631126 <p> GAZA , - Israel will allow the export of commercial goods from the Gaza Strip through a main border crossing from Sunday after a days-long ban for
```

Classification:

```plain text
gb -> North
```

Output file:

```plain text
corpus/02_now_organised/global_north_2023_09/gb/101631126.txt
```

Output file content:

```plain text
<p> GAZA , - Israel will allow the export of commercial goods from the Gaza Strip through a main border crossing from Sunday after a days-long ban for
```

---

## 16.2 Filename country code examples

| Input filename  | Extracted country code |
|-----------------|------------------------|
| `23-09-gb.txt`  | `gb`                   |
| `23-09-ph.txt`  | `ph`                   |
| `21-07-us1.txt` | `us`                   |
| `21-07-us2.txt` | `us`                   |
| `22-06-ca.txt`  | `ca`                   |

---

## 16.3 Example `duplicate_article_ids.tsv`

```plain text
article_id	occurrence_count	first_article_file	first_line_number	first_year_month	first_country_code	all_occurrences
101631126	2	23-09-text/23-09-gb.txt	1	2023-09	gb	23-09-text/23-09-gb.txt:1:2023-09:gb;23-09-text/23-09-ph.txt:44:2023-09:ph
```

---

## 16.4 Example `malformed_selected_article_lines.tsv`

```plain text
article_file	line_number	year_month	country_code	line_preview
23-09-text/23-09-gb.txt	14	2023-09	gb	This line does not begin with an article ID...
```

---

## 16.5 Example `unknown_country_codes.tsv`

```plain text
article_file	year_month	country_code	reason
23-09-text/23-09-xx.txt	2023-09	xx	Country code not found in Global North/South classification
```

---

## 16.6 Example `malformed_article_filenames.tsv`

```plain text
article_file	year_month	reason
23-09-text/notes.txt	2023-09	Filename does not match expected NOW article filename pattern
```

---

## 17. Acceptance Criteria

The programme is considered complete when it satisfies the following criteria.

## 17.1 Command-line execution

The following command must run successfully when the input paths exist:

```shell
python organise_now_articles.py \
    --initial-date 2023-09-01 \
    --final-date 2026-09-15 \
    --global-north-south-classification docs/now_country_codes_north_south.md \
    --input-articles corpus/01_now_dataset/02_now_text \
    --output-articles corpus/02_now_organised
```

---

## 17.2 Output directory creation

The programme must create:

```plain text
corpus/02_now_organised
```

if it does not exist.

---

## 17.3 Month filtering

The programme must process only subdirectories whose inferred year-month is inside the inclusive requested year-month range.

For:

```shell
--initial-date 2023-09-01 --final-date 2026-09-15
```

the programme must include:

```plain text
2023-09
2023-10
...
2026-09
```

The day portions of the CLI dates must not restrict article-level processing.

---

## 17.4 Supported month directory formats

The programme must support both:

```plain text
23-09-text
text-25-01
```

and infer the same kind of `YYYY-MM` value from both.

---

## 17.5 Country code extraction

The programme must correctly extract:

```plain text
gb
ph
us
```

from filenames such as:

```plain text
23-09-gb.txt
23-09-ph.txt
21-07-us1.txt
21-07-us2.txt
```

---

## 17.6 Global North/South organisation

The programme must organise output files according to the classification file.

For example:

```plain text
gb -> global_north_YYYY_MM
ph -> global_south_YYYY_MM
```

---

## 17.7 Article output

Each valid, non-duplicate article line must be written as an individual `.txt` file named:

```plain text
<article_id>.txt
```

The file must contain only the article content after the article ID.

---

## 17.8 Duplicate handling

If the same article ID appears more than once:

- only the first occurrence must be written;
- later occurrences must be skipped;
- the duplicate ID must be recorded in `duplicate_article_ids.tsv`.

---

## 17.9 Malformed selected article lines

Malformed selected article lines must be:

- skipped;
- counted;
- written to `malformed_selected_article_lines.tsv`.

---

## 17.10 Malformed article filenames

Files in selected month directories whose names do not match the expected article filename pattern must be:

- skipped;
- counted;
- written to `malformed_article_filenames.tsv`.

---

## 17.11 Unknown country codes

Files with syntactically valid country codes that are not found in the Global North/South classification must be:

- skipped;
- counted;
- written to `unknown_country_codes.tsv`.

---

## 17.12 Diagnostic files

The programme must create all required diagnostic files even when no records exist beyond the header.

Required diagnostic files:

```plain text
duplicate_article_ids.tsv
malformed_selected_article_lines.tsv
unknown_country_codes.tsv
malformed_article_filenames.tsv
```

---

## 17.13 Log file

The programme must create:

```plain text
organise_now_articles.log
```

inside `--output-articles`.

---

## 17.14 Robustness

Malformed lines, malformed filenames, unknown country codes, duplicate article IDs, and unreadable individual files must not stop the entire programme.

Fatal path or argument errors must stop the programme with a non-zero exit code.

---

## 18. Non-goals for the First Version

The first version should **not** attempt to:

- match articles with NOW source metadata;
- infer publication dates from article content;
- filter by exact day within a month;
- classify countries not present in the classification document;
- clean or normalise article content;
- remove HTML-like tags such as `<p>` or `<h>`;
- combine article files into a single output file;
- preserve the original input directory tree;
- deduplicate article content by text similarity;
- infer country code from article content;
- infer Global North/South classification from country names;
- create metadata summaries beyond diagnostics and logs.

---

## 19. Summary

`organise_now_articles.py` reorganises selected NOW corpus article lines into individual article text files grouped by Global North/South classification, year-month, and country code.

The programme uses the date arguments only at year-month granularity because the source subdirectories encode only year and month. It extracts country codes from filenames, article IDs from `@@` line prefixes, writes only the first occurrence of duplicate article IDs, and produces diagnostic files for duplicates, malformed article lines, malformed filenames, and unknown country codes.
