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
3. Recursively scan the raw NOW source metadata directory.
4. Match metadata rows whose article ID appears in the selected article ID set.
5. Filter matches by publication date using `--initial-date` and `--final-date`.
6. Write a consolidated matched metadata file.
7. Write diagnostic files for unmatched and duplicate article IDs.
8. Produce a log file summarising the process.

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

| Argument | Required | Description |
|---|---:|---|
| `--initial-date` | Yes | First publication date to include, in ISO format: `YYYY-MM-DD`. |
| `--final-date` | Yes | Final publication date to include, in ISO format: `YYYY-MM-DD`. |
| `--input-sources` | Yes | Directory containing raw NOW source metadata files. |
| `--input-articles` | Yes | Directory containing selected NOW article text files. |
| `--match` | Yes | Output directory where matched metadata and diagnostic files will be written. |

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

### 3.1.2 Malformed article lines

A non-empty line in a selected article file that does not contain a valid `@@` article ID at the start must be counted as a malformed article line.

Malformed article lines should not stop the programme.

The programme should log a warning summary, not every malformed line individually unless the number is small.

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

| Column | Output field name | Description |
|---:|---|---|
| 1 | `article_id` | NOW article ID. This is the join key. |
| 2 | `now_field_2` | Unknown or opaque NOW field. Preserve unchanged. |
| 3 | `date_original` | Original NOW date string, expected as `YY-MM-DD`. |
| 4 | `country_code` | NOW country code. Preserve as uppercase or as found. |
| 5 | `source_name` | Publication, vehicle, or source name. |
| 6 | `url` | Article URL. |
| 7 | `title` | Article title. |

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
- optionally record them in a metadata duplicate diagnostic file if implemented.

For the first version, duplicate selected article IDs are mandatory diagnostics. Duplicate metadata diagnostics are optional but recommended.

---

## 6. Output Files

The `--match` argument must be treated as an output directory.

The programme must create this directory if it does not exist.

The recommended output files are:

```plain text
matched_sources.tsv
unmatched_article_ids.tsv
duplicate_article_ids.tsv
find_now_sources_text_matches.log
```


Optionally:

```plain text
duplicate_metadata_matches.tsv
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

---

## 6.4 `find_now_sources_text_matches.log`

The programme must write a log file named:

```plain text
find_now_sources_text_matches.log
```


The log file should be written inside the `--match` output directory.

The programme should also log to the console.

---

## 6.5 Optional `duplicate_metadata_matches.tsv`

If implemented, this file should contain selected article IDs that matched more than one metadata row inside the requested date range.

Recommended columns:

```plain text
article_id
match_count
source_files
article_files
```


This file is optional for the first implementation but useful for corpus auditing.

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
- number of selected article files found;
- number of selected article lines scanned;
- number of selected article IDs found;
- number of unique selected article IDs;
- number of duplicate selected article IDs;
- number of malformed selected article lines;
- number of source metadata files found;
- number of source metadata lines scanned;
- number of matched metadata rows inside date range;
- number of selected article IDs unmatched inside date range;
- number of malformed metadata lines;
- number of source files that could not be read, if any;
- output file paths.

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


---

## 9. Error Handling

## 9.1 Recoverable errors

The programme should continue after recoverable errors such as:

- an unreadable individual file;
- a malformed article line;
- a malformed metadata line;
- an invalid metadata date;
- an output diagnostic issue that does not affect the main output, if safely recoverable.

Recoverable errors must be logged.

## 9.2 Fatal errors

The programme should terminate with non-zero exit code for fatal errors such as:

- invalid command-line dates;
- missing input directories;
- unreadable output directory;
- inability to create the output directory;
- inability to create the main matched output file.

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

Country codes may later be enriched using the project’s country classification table, but that is not required for the first matching programme.

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

| Function | Responsibility |
|---|---|
| `parse_args()` | Parse command-line arguments. |
| `configure_logging()` | Set up console and file logging. |
| `ensure_directory()` | Create output directory if needed. |
| `parse_iso_date()` | Parse CLI dates. |
| `parse_now_date()` | Convert NOW `YY-MM-DD` dates to ISO date objects/strings. |
| `iter_text_files()` | Recursively yield `.txt` files from an input directory. |
| `collect_article_ids()` | Scan selected article files and collect article IDs. |
| `extract_article_id_from_article_line()` | Extract article ID from `@@` article line. |
| `scan_source_metadata()` | Stream source metadata files and write matched rows. |
| `parse_source_metadata_line()` | Parse one tab-separated metadata row. |
| `write_unmatched_article_ids()` | Write unmatched diagnostic file. |
| `write_duplicate_article_ids()` | Write duplicate selected article ID diagnostic file. |
| `main()` | Coordinate the complete programme. |

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
metadata_match_counts: dict[str, int]
```


Optional. Counts how many in-range metadata rows matched each selected article ID.

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

Collect selected article IDs:
    for each .txt file under input articles:
        for each line:
            extract @@ article ID
            store article ID and relative file path
            count malformed lines

Open matched_sources.tsv for writing.

Scan source metadata:
    for each .txt file under input sources:
        for each line:
            quickly extract article ID before first tab
            if article ID not in selected IDs:
                continue

            parse full metadata row
            parse NOW date
            if date is outside date range:
                continue

            write matched metadata row
            add article ID to matched IDs

Write unmatched_article_ids.tsv.

Write duplicate_article_ids.tsv.

Optionally write duplicate_metadata_matches.tsv.

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

### 15.5 Duplicate diagnostics

The programme must create:

```plain text
duplicate_article_ids.tsv
```


containing duplicate article IDs from the selected article text files.

If no duplicate article IDs are found, the file should still be created with only the header row.

### 15.6 Log file

The programme must create:

```plain text
find_now_sources_text_matches.log
```


inside the output directory.

### 15.7 Large-file safety

The programme must process source metadata files line by line and must not read a complete source metadata file into memory.

### 15.8 Date filtering

The programme must use `--initial-date` and `--final-date` as an inclusive date range.

### 15.9 Robustness

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

## 17. Recommended Output Example

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


---

## 18. Summary

`find_now_sources_text_matches.py` should be a streaming metadata matcher for selected NOW corpus articles. Its main design principle is to keep the small selected article ID set in memory while scanning the very large metadata files line by line.

The required CLI should use `--final-date`, not `--end-date`, and the programme should produce a consolidated matched metadata table plus diagnostic files for unmatched and duplicate article IDs.