# Development Specification: `find_now_sources_text_matches.py`

## 1. Purpose

`find_now_sources_text_matches.py` is a Python programme for matching selected NOW corpus article texts with their corresponding source metadata.

The selected article texts are expected to have already been extracted into a smaller dataset by a previous filtering step. Each selected article line begins with an article identifier marked by `@@`, for example:

```plain text
@@41612337 <h> The Gaza prison <p> It is easier to enter...
```


The corresponding metadata is stored separately in NOW source files. Each metadata row is expected to be tab-separated and to begin with the same article ID, for example:

```plain text
86491139	485	20-12-31	ZA	MyBroadband	https://mybroadband.co.za/news/software/380614-bridging-the-gap-between-it-and-lawyers.html	Bridging the gap between IT and lawyers
```


The programme will:

1. Recursively scan the selected article text directory.
2. Extract all selected article IDs from lines beginning with `@@`.
3. Record malformed selected article lines in a diagnostic file.
4. Recursively scan the raw NOW source metadata directory.
5. Match metadata rows whose article ID appears in the selected article ID set.
6. Filter matches by publication date using `--initial-date` and `--final-date`.
7. Write a consolidated matched metadata file.
8. Write diagnostic files for unmatched article IDs, duplicate article IDs, malformed selected article lines, and duplicate metadata matches.
9. Produce a log file summarising the process.

The programme must be designed for large source metadata files and therefore must process metadata files **line by line**, without loading them fully into memory.

---

## 2. Command-line Interface

The programme must be executable from the command line as follows:

```textmate
python find_now_sources_text_matches.py \
    --initial-date 2020-01-01 \
    --final-date 2020-12-31 \
    --input-sources corpus/01_now_dataset_raw/01_now_sources_raw \
    --input-articles corpus/01_now_dataset/02_now_text \
    --match corpus/01_now_dataset/01_now_matched_sources
```


### 2.1 Required arguments

| Argument           | Required | Description                                                                   |
|--------------------|---------:|-------------------------------------------------------------------------------|
| `--initial-date`   |      Yes | First publication date to include, in ISO format: `YYYY-MM-DD`.               |
| `--final-date`     |      Yes | Final publication date to include, in ISO format: `YYYY-MM-DD`.               |
| `--input-sources`  |      Yes | Directory containing raw NOW source metadata files.                           |
| `--input-articles` |      Yes | Directory containing selected NOW article text files.                         |
| `--match`          |      Yes | Output directory where matched metadata and diagnostic files will be written. |

### 2.2 Date range semantics

The date range must be inclusive.

For example:

```textmate
--initial-date 2020-01-01 --final-date 2020-12-31
```


must include articles dated:

```plain text
2020-01-01
2020-12-31
```


and all dates between them.

### 2.3 Invalid argument handling

The programme must terminate with a non-zero exit code if:

- `--initial-date` is not a valid ISO date;
- `--final-date` is not a valid ISO date;
- `--initial-date` is later than `--final-date`;
- `--input-sources` does not exist;
- `--input-sources` is not a directory;
- `--input-articles` does not exist;
- `--input-articles` is not a directory.

The `--match` directory must be created if it does not exist.

---

## 3. Input Data

## 3.1 Selected article text files

The programme must recursively process `.txt` files under `--input-articles`.

The selected article files are expected to contain one article per line, with each article line beginning with an article ID introduced by `@@`.

Example:

```plain text
@@41612337 <h> The Gaza prison <p> It is easier to enter...
@@41613843 <h> The Israeli occupation has helped to cause...
```


### 3.1.1 Article ID format

The article ID must be extracted from the beginning of the line using the following conceptual pattern:

```plain text
^\s*@@(\d+)\b
```


This means:

- optional leading whitespace is allowed;
- the article marker must be `@@`;
- the article ID must consist of one or more digits;
- the article ID must appear at the beginning of the article line after optional whitespace.

### 3.1.2 Malformed selected article lines

A non-empty line in a selected article file that does not contain a valid `@@` article ID at the start must be counted as a malformed selected article line.

Malformed selected article lines should not stop the programme.

Each malformed selected article line must be recorded in:

```plain text
malformed_selected_article_lines.tsv
```


The diagnostic record must include:

- the selected article file path relative to `--input-articles`;
- the line number;
- a short preview of the malformed line.

The line preview should be truncated to avoid creating extremely large diagnostic rows.

---

## 3.2 Raw NOW source metadata files

The programme must recursively process `.txt` files under `--input-sources`.

Each source metadata row is expected to be tab-separated with seven fields:

```plain text
article_id	field_2	date	country_code	source_name	url	title
```


Example:

```plain text
86491139	485	20-12-31	ZA	MyBroadband	https://mybroadband.co.za/news/software/380614-bridging-the-gap-between-it-and-lawyers.html	Bridging the gap between IT and lawyers
```


### 3.2.1 Metadata field interpretation

| Column | Output field name | Description                                          |
|-------:|-------------------|------------------------------------------------------|
|      1 | `article_id`      | NOW article ID. This is the join key.                |
|      2 | `now_field_2`     | Unknown or opaque NOW field. Preserve unchanged.     |
|      3 | `date_original`   | Original NOW date string, expected as `YY-MM-DD`.    |
|      4 | `country_code`    | NOW country code. Preserve as uppercase or as found. |
|      5 | `source_name`     | Publication, vehicle, or source name.                |
|      6 | `url`             | Article URL.                                         |
|      7 | `title`           | Article title.                                       |

The second column must not be interpreted or transformed at this stage. It must be preserved under the output name `now_field_2`.

### 3.2.2 Metadata parsing

Metadata lines should be parsed with a maximum of seven fields.

Conceptually:

```python
fields = line.rstrip("\r\n").split("\t", 6)
```


This ensures that the title remains the seventh field even if it contains unusual text.

### 3.2.3 Malformed metadata lines

A metadata line must be treated as malformed if:

- it has no tab character;
- it contains fewer than seven tab-separated fields;
- its article ID field is empty;
- its date field cannot be parsed as a valid NOW date.

Malformed metadata lines must be counted and skipped.

Malformed metadata lines should not stop the programme unless an input file cannot be opened at all.

---

## 4. Date Handling

## 4.1 Input CLI dates

The command-line dates must use ISO format:

```plain text
YYYY-MM-DD
```


Example:

```plain text
2020-01-01
```


The programme must parse these into date objects for reliable comparison.

## 4.2 NOW metadata dates

NOW metadata dates are expected to use short year format:

```plain text
YY-MM-DD
```


Example:

```plain text
20-12-31
```


The programme must convert these to ISO dates using a 2000-based interpretation:

```plain text
20-12-31 -> 2020-12-31
25-06-01 -> 2025-06-01
```


### 4.2.1 Date output

The matched output must include both:

- `date_original`;
- `date_iso`.

Example:

```plain text
date_original	date_iso
20-12-31	2020-12-31
```


---

## 5. Matching Strategy

## 5.1 Core strategy

The programme must use a two-pass streaming strategy:

1. **Pass 1: selected article files**
   - Recursively scan selected article text files.
   - Extract article IDs from article lines.
   - Store the selected article IDs in memory.
   - Record malformed selected article lines with file path, line number, and line preview.

2. **Pass 2: source metadata files**
   - Recursively scan source metadata files.
   - Read each metadata file line by line.
   - Check whether the metadata article ID is present in the selected article ID set.
   - If not present, skip the row immediately.
   - If present, parse and validate the complete metadata row.
   - Convert and check the date.
   - If the date is inside the inclusive date range, write the row to the matched output.

## 5.2 Memory requirements

The programme must not load full source metadata files into memory.

The programme may keep the following in memory:

- selected article IDs;
- selected article ID to article location mapping;
- matched article IDs;
- duplicate article ID information;
- malformed selected article line records;
- counters and summary statistics.

Article IDs should be stored as strings, not integers.

## 5.3 Duplicate article IDs in selected article files

If the same article ID appears more than once in the selected article files, the programme must:

- retain all known locations for that ID;
- count it as a duplicate selected article ID;
- write it to a duplicate diagnostic file;
- continue processing.

A duplicate should not prevent matching.

## 5.4 Duplicate metadata rows

If the same selected article ID appears in more than one metadata row within the requested date range, the programme should:

- write all matched metadata rows to the main matched output;
- count metadata duplicate matches;
- record them in a metadata duplicate diagnostic file.

---

## 6. Output Files

The `--match` argument must be treated as an output directory.

The programme must create this directory if it does not exist.

The required output files are:

```plain text
matched_sources.tsv
unmatched_article_ids.tsv
duplicate_article_ids.tsv
malformed_selected_article_lines.tsv
duplicate_metadata_matches.tsv
find_now_sources_text_matches.log
```


---

## 6.1 `matched_sources.tsv`

This is the primary output file.

It must contain one row per matched metadata row whose:

- article ID occurs in the selected article text files;
- metadata publication date falls inside the inclusive date range.

### 6.1.1 Required columns

The file must be UTF-8 encoded, tab-separated, and contain a header row.

Required columns:

```plain text
article_id
now_field_2
date_original
date_iso
country_code
source_name
url
title
article_file
source_file
```


Recommended header:

```plain text
article_id	now_field_2	date_original	date_iso	country_code	source_name	url	title	article_file	source_file
```


### 6.1.2 `article_file`

The `article_file` column must contain the relative path from `--input-articles` to the selected article file where the article ID was found.

Example:

```plain text
text-20-01/20_01-gb.txt
```


If the article ID appeared in multiple article files, the paths may be joined with a semicolon:

```plain text
text-20-01/20_01-gb.txt;text-20-01/20_01-gb-duplicate.txt
```


### 6.1.3 `source_file`

The `source_file` column must contain the relative path from `--input-sources` to the metadata file where the matching source row was found.

Example:

```plain text
now-sources-2020.txt
```


---

## 6.2 `unmatched_article_ids.tsv`

This diagnostic file must contain selected article IDs for which no matching metadata row was found inside the requested date range.

### 6.2.1 Required columns

```plain text
article_id
article_file
```


Recommended header:

```plain text
article_id	article_file
```


### 6.2.2 Meaning of “unmatched”

For the first version, an article ID should be considered unmatched if it does not produce a row in `matched_sources.tsv`.

This means that an article ID can be unmatched because:

- it does not exist in the source metadata files;
- it exists in the source metadata files but outside the requested date range;
- its metadata row is malformed and therefore skipped.

---

## 6.3 `duplicate_article_ids.tsv`

This diagnostic file must contain article IDs that occur more than once in the selected article text files.

### 6.3.1 Required columns

```plain text
article_id
count
article_files
```


Recommended header:

```plain text
article_id	count	article_files
```


Where:

- `count` is the number of occurrences found in selected article files;
- `article_files` is a semicolon-separated list of relative article file paths.

If no duplicate article IDs are found, the file should still be created with only the header row.

---

## 6.4 `malformed_selected_article_lines.tsv`

This diagnostic file must contain selected article lines that could not be parsed as valid article lines.

A selected article line is malformed when it is non-empty but does not begin with a valid article ID introduced by `@@`.

### 6.4.1 Required columns

```plain text
article_file
line_number
line_preview
```


Recommended header:

```plain text
article_file	line_number	line_preview
```


Where:

- `article_file` is the path of the selected article file relative to `--input-articles`;
- `line_number` is the 1-based line number in that selected article file;
- `line_preview` is a short, tab-safe preview of the malformed line.

### 6.4.2 Line preview handling

The line preview should:

- strip leading and trailing whitespace;
- replace tab characters with spaces;
- be truncated to a reasonable maximum length, e.g. 250 characters.

If no malformed selected article lines are found, the file should still be created with only the header row.

---

## 6.5 `duplicate_metadata_matches.tsv`

This diagnostic file must contain selected article IDs that matched more than one metadata row inside the requested date range.

### 6.5.1 Required columns

```plain text
article_id
match_count
source_files
article_files
```


Recommended header:

```plain text
article_id	match_count	source_files	article_files
```


Where:

- `article_id` is the selected NOW article ID;
- `match_count` is the number of matched metadata rows for that article ID;
- `source_files` is a semicolon-separated list of metadata source files in which the article ID was matched;
- `article_files` is a semicolon-separated list of selected article files in which the article ID was found.

If no duplicate metadata matches are found, the file should still be created with only the header row.

---

## 6.6 `find_now_sources_text_matches.log`

The programme must write a log file named:

```plain text
find_now_sources_text_matches.log
```


The log file should be written inside the `--match` output directory.

The programme should also log to the console.

---

## 7. Logging Requirements

The programme must use standard logging levels:

- `INFO`
- `WARNING`
- `ERROR`

## 7.1 Required log information

The log must include:

- programme start;
- programme completion;
- resolved input and output paths;
- initial date;
- final date;
- path to `matched_sources.tsv`;
- path to `unmatched_article_ids.tsv`;
- path to `duplicate_article_ids.tsv`;
- path to `malformed_selected_article_lines.tsv`;
- path to `duplicate_metadata_matches.tsv`;
- path to `find_now_sources_text_matches.log`;
- number of selected article files found;
- number of selected article lines scanned;
- number of selected article IDs found;
- number of unique selected article IDs;
- number of duplicate selected article IDs;
- number of duplicate selected article IDs written;
- number of malformed selected article lines;
- number of malformed selected article lines written;
- number of unreadable selected article files;
- number of source metadata files found;
- number of source metadata lines scanned;
- number of matched metadata rows inside date range;
- number of selected article IDs unmatched inside date range;
- number of duplicate metadata matches written;
- number of malformed metadata lines;
- number of unreadable source metadata files.

## 7.2 Logging volume

The programme must avoid logging every non-matching metadata row.

For very large files, logging per skipped row would be too slow and would create excessively large logs.

The programme should log summaries and recoverable errors.

---

## 8. Performance Requirements

The programme must be suitable for raw NOW metadata files that may be around or above 1 GB.

Therefore:

1. Source metadata files must be read line by line.
2. Full metadata files must not be loaded into memory.
3. The selected article ID set may be kept in memory.
4. Metadata lines whose article ID is not selected should be skipped as early as possible.
5. Full tab-splitting of metadata rows should be done only for candidate rows whose article ID occurs in the selected article ID set, where practical.

Recommended fast metadata checking strategy:

```plain text
For each metadata line:
    find first tab
    extract article_id
    if article_id not in selected_ids:
        continue
    fully parse the row
    validate date
    apply date range
    write matched row
```


The programme may store malformed selected article line records in memory because the selected article dataset is already a reduced subset. If malformed selected article lines become numerous in a future dataset, this can be changed to streaming diagnostic writes.

---

## 9. Error Handling

## 9.1 Recoverable errors

The programme should continue after recoverable errors such as:

- an unreadable individual selected article file;
- an unreadable individual source metadata file;
- a malformed selected article line;
- a malformed metadata line;
- an invalid metadata date;
- a duplicate selected article ID;
- a duplicate metadata match.

Recoverable errors must be logged or written to diagnostic files where applicable.

## 9.2 Fatal errors

The programme should terminate with non-zero exit code for fatal errors such as:

- invalid command-line dates;
- missing input directories;
- unreadable output directory;
- inability to create the output directory;
- inability to create the main matched output file;
- inability to write required diagnostic output files.

---

## 10. File Encoding and Line Endings

## 10.1 Input files

Input files should be opened with:

```plain text
UTF-8 encoding
errors="replace"
```


This prevents the programme from failing because of occasional invalid byte sequences.

## 10.2 Output files

Output files must be:

- UTF-8 encoded;
- tab-separated where applicable;
- written with LF line endings.

---

## 11. Country Codes and Global North/South Classification

The first implementation should preserve the NOW country code as found in the metadata.

Country codes may later be enriched using a country classification table, but that is not required for the first matching programme.

The matching programme should therefore not depend on Global North/South classification.

Recommended first-version behaviour:

```plain text
country_code = source metadata country code, preserved unchanged
```


Optional later enhancement:

```plain text
country_name
global_region
```


---

## 12. Programme Structure

The implementation should be modular and readable.

Recommended functions:

| Function                                   | Responsibility                                                                                 |
|--------------------------------------------|------------------------------------------------------------------------------------------------|
| `parse_args()`                             | Parse command-line arguments.                                                                  |
| `configure_logging()`                      | Set up console and file logging.                                                               |
| `ensure_directory()`                       | Create output directory if needed.                                                             |
| `parse_iso_date()`                         | Parse CLI dates.                                                                               |
| `parse_now_date()`                         | Convert NOW `YY-MM-DD` dates to ISO date objects/strings.                                      |
| `validate_input_directory()`               | Validate that required input paths exist and are directories.                                  |
| `iter_text_files()`                        | Recursively collect `.txt` files from an input directory.                                      |
| `relative_posix_path()`                    | Convert paths to relative POSIX-style paths for stable TSV output.                             |
| `extract_article_id_from_article_line()`   | Extract article ID from `@@` article line.                                                     |
| `make_line_preview()`                      | Produce a short, tab-safe preview of malformed selected article lines.                         |
| `collect_article_ids()`                    | Scan selected article files, collect article IDs, and record malformed selected article lines. |
| `extract_metadata_article_id_fast()`       | Quickly extract metadata article ID before full row parsing.                                   |
| `parse_source_metadata_line()`             | Parse one tab-separated metadata row.                                                          |
| `write_matched_sources_header()`           | Write the header for the primary matched metadata file.                                        |
| `scan_source_metadata()`                   | Stream source metadata files and write matched rows.                                           |
| `write_unmatched_article_ids()`            | Write unmatched article ID diagnostic file.                                                    |
| `write_duplicate_article_ids()`            | Write duplicate selected article ID diagnostic file.                                           |
| `write_malformed_selected_article_lines()` | Write malformed selected article line diagnostic file.                                         |
| `write_duplicate_metadata_matches()`       | Write duplicate metadata match diagnostic file.                                                |
| `log_output_paths()`                       | Log paths of all output files.                                                                 |
| `main()`                                   | Coordinate the complete programme.                                                             |

---

## 13. Data Structures

Recommended in-memory structures:

```python
selected_article_locations: dict[str, list[str]]
```


Maps article IDs to one or more relative article file paths.

```python
selected_ids: set[str]
```


Can be derived from `selected_article_locations.keys()`.

```python
matched_ids: set[str]
```


Tracks selected article IDs that produced at least one matched metadata row inside the requested date range.

```python
metadata_match_counts: Counter[str]
```


Counts how many in-range metadata rows matched each selected article ID.

```python
metadata_match_source_files: dict[str, set[str]]
```


Maps article IDs to source metadata files where in-range matches were found.

```python
malformed_selected_article_line_records: list[tuple[str, int, str]]
```


Stores malformed selected article line diagnostics as:

```plain text
article_file, line_number, line_preview
```


---

## 14. Expected Processing Logic

## 14.1 High-level pseudocode

```plain text
Parse command-line arguments.

Resolve paths.

Validate:
    initial date
    final date
    input source directory
    input article directory

Create match output directory.

Configure logging.

Define output paths:
    matched_sources.tsv
    unmatched_article_ids.tsv
    duplicate_article_ids.tsv
    malformed_selected_article_lines.tsv
    duplicate_metadata_matches.tsv
    find_now_sources_text_matches.log

Log output paths.

Collect selected article IDs:
    for each .txt file under input articles:
        for each line with 1-based line number:
            skip blank lines
            extract @@ article ID
            if article ID is valid:
                store article ID and relative file path
            otherwise:
                count malformed selected article line
                record:
                    article_file
                    line_number
                    line_preview

Open matched_sources.tsv for writing.

Scan source metadata:
    for each .txt file under input sources:
        for each non-blank line:
            quickly extract article ID before first tab
            if article ID is missing:
                count malformed metadata line
                continue
            if article ID not in selected IDs:
                continue

            parse full metadata row
            parse NOW date
            if row or date is malformed:
                count malformed metadata line
                continue

            if date is outside date range:
                continue

            write matched metadata row
            add article ID to matched IDs
            increment metadata match count
            record source metadata file for the matched article ID

Write unmatched_article_ids.tsv.

Write duplicate_article_ids.tsv.

Write malformed_selected_article_lines.tsv.

Write duplicate_metadata_matches.tsv.

Log summary.

Exit with code 0 if successful.
```


---

## 15. Acceptance Criteria

The programme is considered complete when it satisfies the following criteria.

### 15.1 Command-line execution

The following command must run successfully when the input directories exist:

```textmate
python find_now_sources_text_matches.py \
    --initial-date 2020-01-01 \
    --final-date 2020-12-31 \
    --input-sources corpus/01_now_dataset_raw/01_now_sources_raw \
    --input-articles corpus/01_now_dataset/02_now_text \
    --match corpus/01_now_dataset/01_now_matched_sources
```


### 15.2 Output directory

The output directory must be created if it does not exist.

### 15.3 Matched metadata

The programme must create:

```plain text
matched_sources.tsv
```


with the required header and one row per in-range metadata match.

### 15.4 Unmatched diagnostics

The programme must create:

```plain text
unmatched_article_ids.tsv
```


with selected article IDs that did not produce in-range metadata matches.

### 15.5 Duplicate selected article diagnostics

The programme must create:

```plain text
duplicate_article_ids.tsv
```


containing duplicate article IDs from the selected article text files.

If no duplicate article IDs are found, the file should still be created with only the header row.

### 15.6 Malformed selected article line diagnostics

The programme must create:

```plain text
malformed_selected_article_lines.tsv
```


containing malformed selected article lines.

If no malformed selected article lines are found, the file should still be created with only the header row.

### 15.7 Duplicate metadata diagnostics

The programme must create:

```plain text
duplicate_metadata_matches.tsv
```


containing selected article IDs that matched more than one in-range metadata row.

If no duplicate metadata matches are found, the file should still be created with only the header row.

### 15.8 Log file

The programme must create:

```plain text
find_now_sources_text_matches.log
```


inside the output directory.

### 15.9 Large-file safety

The programme must process source metadata files line by line and must not read a complete source metadata file into memory.

### 15.10 Date filtering

The programme must use `--initial-date` and `--final-date` as an inclusive date range.

### 15.11 Robustness

Malformed lines must be counted and skipped without stopping the whole programme.

---

## 16. Non-goals for the First Version

The first version should **not** attempt to:

- classify articles as relevant or irrelevant beyond the previous seed-term selection;
- enrich country codes with Global North/South categories;
- rewrite or copy the article text files;
- combine full article text and metadata into one large file;
- deduplicate article text;
- infer article dates from file names;
- interpret the meaning of `now_field_2`.

These can be added later if needed.

---

## 17. Recommended Output Examples

Example `matched_sources.tsv`:

```plain text
article_id	now_field_2	date_original	date_iso	country_code	source_name	url	title	article_file	source_file
41612337	123	20-01-01	2020-01-01	GB	Example News	https://example.com/article	The Gaza prison	text-20-01/20_01-gb.txt	now-sources-2020.txt
```


Example `unmatched_article_ids.tsv`:

```plain text
article_id	article_file
41613843	text-20-01/20_01-gb.txt
```


Example `duplicate_article_ids.tsv`:

```plain text
article_id	count	article_files
83060635	2	text-20-01/20_01-gb.txt;text-20-01/20_01-gb-copy.txt
```


Example `malformed_selected_article_lines.tsv`:

```plain text
article_file	line_number	line_preview
text-11-02/11-02-au.txt	2	This line does not begin with an article ID...
```


Example `duplicate_metadata_matches.tsv`:

```plain text
article_id	match_count	source_files	article_files
83060635	2	now-sources-2020.txt;sources-20-01.txt	text-20-01/20_01-gb.txt
```


---

## 18. Summary

`find_now_sources_text_matches.py` is a streaming metadata matcher for selected NOW corpus articles. Its main design principle is to keep the smaller selected article ID set in memory while scanning the much larger metadata files line by line.

The programme uses `--final-date`, not `--end-date`, and produces a consolidated matched metadata table plus diagnostic files for unmatched article IDs, duplicate selected article IDs, malformed selected article lines, and duplicate metadata matches.