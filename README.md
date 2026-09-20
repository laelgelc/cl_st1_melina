# Corpus Linguistics - Study 1 - Melina

## Phase 1 - Data Collection, Screening and Sampling

This repository contains the first phase of a corpus linguistics study using the [News on the Web (NOW)](https://www.english-corpora.org/corpora.asp) corpus. Phase 1 focuses on identifying, organising, screening, inspecting and sampling English-language news articles relevant to Palestine/Gaza-related discourse.

The current phase is designed to:

- extract NOW corpus articles containing a seed search term;
- match selected article files with their source metadata;
- organise articles by date and country classification;
- generate structured corpus files for downstream analysis;
- apply LLM-assisted screening to identify articles relevant to the study scope;
- inspect and flatten the LLM-screened dataset for analysis;
- identify the main recommended corpus;
- enrich the recommended corpus with word-count and sampling metadata;
- create IQR-filtered and IQR-capped corpus subsets for later phases of analysis.

The broader research focus is on diachronic media discourse around Palestine/Gaza, with particular attention to variation across Global North and Global South media contexts and to the requirements of Lexical Multidimensional Analysis.

---

### Project Structure

The active Phase 1 directory is:
```text
cl_st1_ph1_melina/
```
The repository currently includes three phase directories:
```text
cl_st1_melina/
├── cl_st1_ph1_melina/
├── cl_st1_ph2_melina/
├── cl_st1_ph3_melina/
├── docs/
├── LICENSE
└── README.md
```
Key Phase 1 areas include:
```text
cl_st1_ph1_melina/
├── corpus/
│   ├── 01_now_dataset/
│   ├── 02_now_organised/
│   ├── 03_now_screened/
│   ├── palestine_now.ndjson
│   ├── palestine_now.tsv
│   ├── palestine_now.xlsx
│   ├── palestine_now_main.ndjson.gz
│   ├── palestine_now_main.tsv
│   └── palestine_now_main.xlsx
├── docs/
│   ├── corpus_sampling_and_analysis_strategy.md
│   ├── media_discourse_analysis_on_the_palestinian_conflict.md
│   └── now_country_codes_north_south.md
├── env/
├── llm_screening_prompts/
├── cl_st1_ph1_melina.ipynb
├── cl_st1_ph1_melina_pipeline.md
├── select_now_files.py
├── find_now_sources_text_matches.py
├── organise_now_articles.py
├── llm_screening.py
└── run_python_ec2.sh
```
The later phase directories receive sampled article files from Phase 1:
```text
cl_st1_ph2_melina/
└── corpus/
    └── 04_now_screened_iqr_cap/

cl_st1_ph3_melina/
└── corpus/
    └── 04_now_screened_iqr/
```
---

### Global North/South Classification

The project classifies NOW corpus country codes into Global North and Global South categories using:
```text
cl_st1_ph1_melina/docs/now_country_codes_north_south.md
```
Current classification:

| Code | Country                        | Global |
|:-----|:-------------------------------|:-------|
| au   | Australia                      | North  |
| bd   | Bangladesh                     | South  |
| ca   | Canada                         | North  |
| gb   | Great Britain (United Kingdom) | North  |
| gh   | Ghana                          | South  |
| hk   | Hong Kong                      | North  |
| ie   | Ireland                        | North  |
| in   | India                          | South  |
| jm   | Jamaica                        | South  |
| ke   | Kenya                          | South  |
| lk   | Sri Lanka                      | South  |
| my   | Malaysia                       | South  |
| ng   | Nigeria                        | South  |
| nz   | New Zealand                    | North  |
| ph   | Philippines                    | South  |
| pk   | Pakistan                       | South  |
| sg   | Singapore                      | North  |
| tz   | Tanzania                       | South  |
| us   | United States                  | North  |
| za   | South Africa                   | South  |

---

### Workflow Overview

Commands should be run from the Phase 1 directory unless otherwise noted:
```shell
cd cl_st1_ph1_melina
```
---

### 1. Select NOW Articles by Seed Term

The first step filters raw NOW text files for articles containing the target seed term, currently centred on `gaza`.
```shell
python select_now_files.py \
    --input corpus/01_now_dataset_raw/02_now_text_raw \
    --output corpus/01_now_dataset/02_now_text
```
The extraction process recursively scans raw NOW text files, filters `.txt` files for whole-word, case-insensitive matches, and preserves the original directory structure in the output.

Execution details are recorded in:
```text
select_now_files.log
```
---

### 2. Match NOW Sources and Article Files

The next step links selected article files with NOW source metadata over a specified date range.

Example test run for 2020:
```shell
python find_now_sources_text_matches.py \
    --initial-date 2020-01-01 \
    --final-date 2020-12-31 \
    --input-sources corpus/01_now_dataset_raw/01_now_sources_raw \
    --input-articles corpus/01_now_dataset/02_now_text \
    --match corpus/01_now_dataset/01_now_matched_sources_2020_test
```
Example run for the main study period:
```shell
python find_now_sources_text_matches.py \
    --initial-date 2023-09-01 \
    --final-date 2026-09-14 \
    --input-sources corpus/01_now_dataset_raw/01_now_sources_raw \
    --input-articles corpus/01_now_dataset/02_now_text \
    --match corpus/01_now_dataset/01_now_matched_sources_2023_2026_test
```
The matching stage produces diagnostic files such as:
```text
matched_sources.tsv
unmatched_article_ids.tsv
duplicate_article_ids.tsv
duplicate_metadata_matches.tsv
malformed_selected_article_lines.tsv
find_now_sources_text_matches.log
```
---

### 3. Organise NOW Articles

Matched articles are organised into a structured corpus using the study date range and the Global North/South country classification document.
```shell
python organise_now_articles.py \
    --initial-date 2023-09-01 \
    --final-date 2026-09-15 \
    --global-north-south-classification docs/now_country_codes_north_south.md \
    --input-articles corpus/01_now_dataset/02_now_text \
    --output-articles corpus/02_now_organised
```
The organisation stage writes individual article files under:
```text
corpus/02_now_organised/
```
The organised structure follows the pattern:
```text
corpus/02_now_organised/<global_position>_<year_month>/<country_code>/<article_id>.txt
```
Example:
```text
corpus/02_now_organised/global_north_2023_09/ca/101993957.txt
```
The organised corpus also produces consolidated files:
```text
corpus/palestine_now.ndjson
corpus/palestine_now.tsv
corpus/palestine_now.xlsx
```
The organisation stage completed with the following key results:

| Metric                                      | Count   |
|---------------------------------------------|--------:|
| Selected month subdirectories processed     |      22 |
| Article files found in selected directories |     495 |
| Selected article lines scanned              | 117,747 |
| Valid article lines found                   | 117,747 |
| Unique article IDs written                  | 117,519 |
| Duplicate article IDs found                 |     228 |
| Duplicate article occurrences skipped       |     228 |
| Malformed selected article lines found      |       0 |
| Unknown country code records                |       0 |
| Malformed article filename records          |       0 |
| Output article files written                | 117,519 |

Diagnostic files from this stage include:
```text
corpus/02_now_organised/duplicate_article_ids.tsv
corpus/02_now_organised/malformed_selected_article_lines.tsv
corpus/02_now_organised/unknown_country_codes.tsv
corpus/02_now_organised/malformed_article_filenames.tsv
corpus/02_now_organised/organise_now_articles.log
```
---

### 4. LLM-Assisted Screening

The project includes an LLM screening stage to assess whether organised articles are relevant to the research focus.

Screening outputs are stored under:
```text
corpus/03_now_screened/
```
A completed screening run directory is:
```text
corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna/
```
This directory contains structured screening results and run metadata, including:
```text
screening_json/
llm_screening.log
llm_screening_failures.ndjson
llm_screening_invalid_responses.ndjson
llm_screening_manifest.json
llm_screening_summary.json
palestine_now_screened.ndjson.gz
```
The full production screening run completed successfully on 2026-09-16 using model `gpt-5.6-luna`.

Final production run:
```text
run_id=20260916T015024Z_0e1ea2f1
```
Final run status:

| Metric                                  | Count   |
|-----------------------------------------|--------:|
| Manifest rows                           | 117,519 |
| Newly succeeded articles                | 117,219 |
| Previously completed / skipped articles |     300 |
| Failed articles                         |       0 |
| Invalid responses                       |       0 |
| Total successfully screened articles    | 117,519 |

The final consolidated screened output is stored as a compressed NDJSON file:
```text
corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna/palestine_now_screened.ndjson.gz
```
The uncompressed NDJSON output exceeded GitHub's standard file-size limit, so the repository stores the compressed `.ndjson.gz` version.

---

### 5. Screening Response Fields

Each screened article contains an `llm_screening` object with the following key fields:

| Field                            | Description                                                                    |
|----------------------------------|--------------------------------------------------------------------------------|
| `category`                       | Screening category, e.g. `CORE`, `PERIPHERAL`, or `EXCLUDE`                    |
| `confidence`                     | Numeric confidence score between 0.0 and 1.0                                   |
| `gaza_role`                      | Degree of Gaza/Palestine relevance                                             |
| `main_topic`                     | Short description of the article's main topic                                  |
| `conflict_relevance`             | Explanation of relevance to the Palestine/Gaza conflict                        |
| `reason`                         | Screening rationale                                                            |
| `multi_article_or_snippet_issue` | Whether the text appears to contain multiple articles or snippet contamination |
| `recommended_for_main_corpus`    | Boolean recommendation for inclusion in the main analytical corpus             |

The most important field for deriving the main corpus is:
```text
recommended_for_main_corpus
```
Only records where this field is `true` are included in the main recommended corpus.

---

### 6. Inspecting the Screened Dataset

The notebook section beginning with **Inspect the df_palestine_now_screened dataset** imports and inspects the screened NDJSON file.

The screened file is newline-delimited JSON, and the `llm_screening` and `llm_screening_metadata` fields contain nested JSON objects. The notebook therefore expands these nested fields into analysis-friendly columns.

Typical import strategy:
```python
import pandas as pd

screened_path = (
    "corpus/03_now_screened/"
    "llm_screening_v2_gpt-5.6-luna/"
    "palestine_now_screened.ndjson.gz"
)

df_raw = pd.read_json(
    screened_path,
    lines=True,
    compression="gzip",
)

screening_cols = pd.json_normalize(
    df_raw["llm_screening"]
).add_prefix("llm_screening__")

metadata_cols = pd.json_normalize(
    df_raw["llm_screening_metadata"]
).add_prefix("llm_screening_metadata__")

df_palestine_now_screened = pd.concat(
    [
        df_raw.drop(columns=["llm_screening", "llm_screening_metadata"]),
        screening_cols,
        metadata_cols,
    ],
    axis=1,
)
```
This creates columns such as:
```text
llm_screening__category
llm_screening__confidence
llm_screening__gaza_role
llm_screening__recommended_for_main_corpus
llm_screening_metadata__status
llm_screening_metadata__model
llm_screening_metadata__screened_at
```
---

### 7. Main Recommended Corpus

The main recommended corpus is created from the screened dataset by retaining only records where:
```text
llm_screening__recommended_for_main_corpus == True
```
This produces the main analysis DataFrame:
```text
df_palestine_now_main
```
The DataFrame is then enriched with additional fields for sampling and later analytical use.

---

### 8. Word Count Enrichment

The `df_palestine_now_main` DataFrame is enriched with a `word_count` column placed immediately to the right of `filepath`.

The `word_count` column is used to inspect article-length distribution and to identify articles that fall within the interquartile range.

The notebook uses this field to:

- describe the distribution of article lengths;
- generate boxplots;
- identify extremely short or extremely long records;
- restrict some analytical subsets to comparable article lengths.

Useful descriptive checks include:
```python
df_palestine_now_main["word_count"].describe()
```
and:
```python
df_palestine_now_main["word_count"].plot(kind="box", vert=False)
```
---

### 9. IQR-Based Sampling Fields

Two boolean sampling fields are added to `df_palestine_now_main`.

#### 9.1 `within_word_count_iqr`

The boolean field:
```text
within_word_count_iqr
```
indicates whether an article's `word_count` falls within the interquartile range of the main recommended corpus.

That is, it is `True` when:
```text
Q1 <= word_count <= Q3
```
where:

- `Q1` is the 25th percentile of `word_count`;
- `Q3` is the 75th percentile of `word_count`.

This field identifies the IQR-filtered analysis corpus.

The IQR-filtered subset is intended to reduce the influence of extreme article lengths while retaining a broad, naturally distributed set of recommended articles.

The IQR-filtered corpus contains:
```text
35,781 articles
```
#### 9.2 `within_word_count_iqr_cap`

The boolean field:
```text
within_word_count_iqr_cap
```
indicates whether an article is part of a reproducible group-capped sample drawn from the IQR-filtered subset.

This field is `True` for articles that satisfy both conditions:
```text
within_word_count_iqr == True
```
and are selected after applying a reproducible per-group cap of:
```text
815 articles per group
```
The sampling is random but reproducible through a fixed random seed.

This field identifies the IQR-capped robustness corpus, designed to limit the dominance of highly represented `group` categories while preserving as much data as possible.

---

### 10. Exported Main Corpus Files

The enriched `df_palestine_now_main` DataFrame is exported to the `corpus/` directory in three formats:
```text
corpus/palestine_now_main.ndjson.gz
corpus/palestine_now_main.tsv
corpus/palestine_now_main.xlsx
```
The NDJSON file is compressed with gzip:
```text
palestine_now_main.ndjson.gz
```
The TSV and XLSX files remain uncompressed for easier inspection and spreadsheet use.

These exported files include the enriched sampling fields:
```text
word_count
within_word_count_iqr
within_word_count_iqr_cap
```
---

### 11. Phase 2 and Phase 3 Corpus Exports

The notebook also copies selected article text files into later phase directories while preserving the original subdirectory structure below `corpus/02_now_organised/`.

#### 11.1 Phase 2: IQR-Capped Corpus

Files where:
```text
within_word_count_iqr_cap == True
```
are copied to:
```text
../cl_st1_ph2_melina/corpus/04_now_screened_iqr_cap/
```
The original path structure is mirrored.

Example source:
```text
corpus/02_now_organised/global_north_2023_09/ca/101993957.txt
```
Example destination:
```text
../cl_st1_ph2_melina/corpus/04_now_screened_iqr_cap/global_north_2023_09/ca/101993957.txt
```
This corpus is intended for balanced or capped robustness analysis.

#### 11.2 Phase 3: IQR-Filtered Corpus

Files where:
```text
within_word_count_iqr == True
```
are copied to:
```text
../cl_st1_ph3_melina/corpus/04_now_screened_iqr/
```
The original path structure is mirrored.

Example source:
```text
corpus/02_now_organised/global_north_2023_09/ca/101993957.txt
```
Example destination:
```text
../cl_st1_ph3_melina/corpus/04_now_screened_iqr/global_north_2023_09/ca/101993957.txt
```
This corpus is intended as the main IQR-filtered analysis corpus.

---

### 12. Corpus Sampling and Analysis Strategy

The sampling strategy distinguishes between **discursive salience** and **lexical-discursive patterning**.

The project therefore does not treat one single corpus as sufficient for every analytical purpose. Instead, it maintains multiple analytically distinct corpus layers.

#### 12.1 Full Main Corpus

The full recommended corpus is represented by:
```text
corpus/palestine_now_main.tsv
corpus/palestine_now_main.xlsx
corpus/palestine_now_main.ndjson.gz
```
This corpus includes all articles recommended for the main corpus by the LLM screening stage.

It is used for:

- documenting data collection;
- article-volume trends;
- corpus coverage;
- salience over time;
- descriptive historical context.

This corpus answers:

> When and where did Palestine/Gaza discourse become more intense?

Article concentration in particular months or groups is not automatically treated as noise. It may reflect historically meaningful periods of tension, including:

- escalation of conflict;
- heightened diplomatic activity;
- elections and policy controversy;
- humanitarian crises;
- protest cycles;
- shifts in national foreign-policy discourse;
- heightened salience of Palestine/Gaza in domestic politics.

#### 12.2 IQR-Filtered Corpus

The IQR-filtered corpus is identified through:
```text
within_word_count_iqr == True
```
It is also copied to:
```text
../cl_st1_ph3_melina/corpus/04_now_screened_iqr/
```
This subset is used as a primary quality-controlled corpus for Lexical Multidimensional Analysis because it controls for extreme text length while preserving much of the natural diachronic and geopolitical distribution.

It answers:

> Among comparable article-length texts, what lexical-discursive patterns emerge?

#### 12.3 IQR-Capped Corpus

The IQR-capped corpus is identified through:
```text
within_word_count_iqr_cap == True
```
It is also copied to:
```text
../cl_st1_ph2_melina/corpus/04_now_screened_iqr_cap/
```
This subset applies a reproducible cap of 815 articles per `group` among articles already inside the word-count IQR.

It is used for:

- robustness checking;
- limiting the influence of highly represented time/geopolitical groups;
- checking whether LMDA dimensions are stable under controlled sampling;
- comparing Global North/South trajectories when no group dominates the sample.

It answers:

> Do the same discursive dimensions hold when no group or month dominates the sample?

---

### 13. Rationale for Multiple Corpus Versions

The project adopts the following methodological position:

> The study distinguishes between discursive salience and lexical-discursive patterning. Article-volume concentrations are retained in descriptive diachronic analyses because they reflect historically meaningful moments of intensified media attention. For lexical multidimensional analysis, however, a controlled IQR-filtered and stratified sample is used to reduce the influence of extreme text length and disproportionate representation of specific time periods or geopolitical groups. Results from the proportionate corpus and the balanced corpus are compared as a robustness check.

This avoids a false choice between:

> The imbalance is bias.

and:

> The imbalance is historically meaningful.

In this project, imbalance may be both:

- meaningful as evidence of historical and discursive salience;
- potentially biasing for lexical modelling if overrepresented groups dominate the extracted dimensions.

The recommended strategy is therefore:

> Preserve concentration for historical/discursive salience, but use IQR filtering and capped stratified sampling for Lexical Multidimensional Analysis robustness.

---

### 14. Lexical Multidimensional Analysis Considerations

Because the project uses Lexical Multidimensional Analysis, corpus composition is especially important.

Potential sources of distortion include:

- dominant time periods;
- dominant Global North or Global South groups;
- repeated wire-service language;
- recurring event-specific vocabulary;
- source-specific style;
- genre mixture, such as news reports, opinion pieces, live blogs, syndicated reports and commentary;
- article-length variation.

The IQR and IQR-capped fields are intended to support comparison between:
```text
full recommended corpus
IQR-filtered corpus
IQR-capped corpus
```
This allows later analysis to assess whether extracted lexical dimensions are robust across corpus configurations.

If results are similar across the IQR-filtered and IQR-capped corpora, findings are more robust. If results differ, that difference is analytically meaningful because it suggests that article volume, temporal salience or group concentration is shaping the lexical dimensions.

---

### 15. Main Outputs

Important generated outputs include:

| Output                                                                                  | Description                                                                   |
|-----------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| `corpus/01_now_dataset/`                                                                | Filtered NOW files selected by seed-term matching                             |
| `corpus/02_now_organised/`                                                              | Organised article corpus by date/source metadata and Global North/South group |
| `corpus/palestine_now.ndjson`                                                           | Main organised manifest before LLM screening                                  |
| `corpus/palestine_now.tsv`                                                              | Tabular export of the organised corpus                                        |
| `corpus/palestine_now.xlsx`                                                             | Spreadsheet export of the organised corpus                                    |
| `corpus/03_now_screened/`                                                               | LLM-screened article outputs                                                  |
| `corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna/palestine_now_screened.ndjson.gz` | Final compressed LLM-screened output                                          |
| `corpus/palestine_now_main.ndjson.gz`                                                   | Final compressed enriched recommended main corpus                             |
| `corpus/palestine_now_main.tsv`                                                         | Final enriched recommended main corpus in TSV format                          |
| `corpus/palestine_now_main.xlsx`                                                        | Final enriched recommended main corpus in XLSX format                         |
| `../cl_st1_ph2_melina/corpus/04_now_screened_iqr_cap/`                                  | Copied article files for the IQR-capped robustness corpus                     |
| `../cl_st1_ph3_melina/corpus/04_now_screened_iqr/`                                      | Copied article files for the IQR-filtered analysis corpus                     |
| `llm_screening_summary.json`                                                            | Summary of LLM screening run                                                  |
| `llm_screening_failures.ndjson`                                                         | Failed screening items                                                        |
| `llm_screening_invalid_responses.ndjson`                                                | Invalid or unparsable model responses                                         |

---

### 16. LLM Screening Commands

#### Dry Run

Use a dry run to validate configuration before making API calls or generating full screening output.
```shell
python llm_screening.py \
    --manifest corpus/palestine_now.ndjson \
    --output corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna \
    --prompt llm_screening_prompts/llm_screening_v2.md \
    --model gpt-5.6-luna \
    --limit 10 \
    --dry-run
```
#### Initial Test Run
```shell
python llm_screening.py \
    --manifest corpus/palestine_now.ndjson \
    --output corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna \
    --prompt llm_screening_prompts/llm_screening_v2.md \
    --model gpt-5.6-luna \
    --limit 10
```
#### Parallel Test Run
```shell
python llm_screening.py \
    --manifest corpus/palestine_now.ndjson \
    --output corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna \
    --prompt llm_screening_prompts/llm_screening_v2.md \
    --model gpt-5.6-luna \
    --limit 200 \
    --workers 20 \
    --resume \
    --max-output-tokens 1000
```
#### Full Screening Run
```shell
python llm_screening.py \
    --manifest corpus/palestine_now.ndjson \
    --output corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna \
    --prompt llm_screening_prompts/llm_screening_v2.md \
    --model gpt-5.6-luna \
    --workers 20 \
    --resume \
    --max-output-tokens 1000 \
    --max-retries 5
```
#### Production Run on EC2

For long-running production screening, the pipeline can be executed on an EC2 instance:
```shell
bash run_python_ec2.sh \
    llm_screening.py \
    --manifest corpus/palestine_now.ndjson \
    --output corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna \
    --prompt llm_screening_prompts/llm_screening_v2.md \
    --model gpt-5.6-luna \
    --workers 20 \
    --resume \
    --max-output-tokens 1000 \
    --max-retries 5
```
---

### 17. Corpus Scope

The working corpus is built from NOW articles containing the `gaza` seed term and is organised for a study period beginning in September 2023.

The corpus includes articles from multiple national source files and supports comparative analysis across:

- publication time;
- country code;
- Global North/South classification;
- screened relevance category;
- article length;
- IQR-filtered inclusion;
- IQR-capped inclusion.

The corpus contains news reports, opinion pieces, syndicated content, live updates, commentary and repeated wire-service material. These characteristics make deduplication, source matching, metadata preservation, length control and relevance screening important.

---

### 18. Documentation

Additional workflow and methodological notes are maintained in the Phase 1 directory:
```text
cl_st1_ph1_melina_pipeline.md
select_now_files.md
find_now_sources_text_matches.md
organise_now_articles.md
llm_screening.md
docs/corpus_sampling_and_analysis_strategy.md
docs/media_discourse_analysis_on_the_palestinian_conflict.md
docs/now_country_codes_north_south.md
```
Key methodological sampling guidance is stored in:
```text
docs/corpus_sampling_and_analysis_strategy.md
```
---

### 19. Reproducibility Notes

- Commands should be run from `cl_st1_ph1_melina/`.
- Generated logs and manifests should be retained for auditability.
- LLM screening runs should use `--resume` when continuing an interrupted or partial run.
- Failed and invalid LLM responses are written separately so they can be reviewed and retried.
- Timestamped screening manifests are preserved to document individual screening attempts.
- The final screened NDJSON and main corpus NDJSON are stored in compressed `.ndjson.gz` format where appropriate.
- Sampling fields are retained in `corpus/palestine_now_main.tsv`, `corpus/palestine_now_main.xlsx` and `corpus/palestine_now_main.ndjson.gz`.
- The IQR-capped corpus uses reproducible random sampling with a fixed random seed.
- The copied Phase 2 and Phase 3 article directories preserve the original organised corpus subdirectory structure.
- The full recommended corpus, the IQR-filtered corpus and the IQR-capped corpus should be treated as analytically distinct resources.

---

### 20. License

See `LICENSE`.

## Phase 2 - Lexical Multi-dimensional Analysis (IQR-Capped)

The Lexical Multi-dimensional Analysis (LMDA) was processed according to the corresponding procedures.

Please refer to: [cl_st1_ph2_melina_pipeline_description.md](https://github.com/laelgelc/cl_st1_melina/blob/main/cl_st1_ph2_melina/cl_st1_ph2_melina_pipeline_description.md)

## Phase 3 - Lexical Multi-dimensional Analysis (IQR-Filtered)

The Lexical Multi-dimensional Analysis (LMDA) was processed according to the corresponding procedures.
