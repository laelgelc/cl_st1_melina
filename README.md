# Corpus Linguistics - Study 1 - Melina

## Phase 1 - Data Collection and Sampling

This repository contains the first phase of a corpus linguistics study using the [News on the Web (NOW)](https://www.english-corpora.org/corpora.asp) corpus. Phase 1 focuses on identifying, organising, and screening English-language news articles relevant to Palestine/Gaza-related discourse.

The current phase is designed to:

- extract NOW corpus articles containing a seed search term;
- match selected article files with their source metadata;
- organise articles by date and country classification;
- generate structured corpus files for downstream analysis;
- apply LLM-assisted screening to identify articles relevant to the study scope.

### Project Structure

The active phase directory is:

```text
cl_st1_ph1_melina/
```

Key project areas include:

```text
cl_st1_ph1_melina/
├── corpus/
│   ├── 01_now_dataset/
│   ├── 02_now_organised/
│   ├── 03_now_screened/
│   ├── palestine_now.ndjson
│   ├── palestine_now.tsv
│   └── palestine_now.xlsx
├── docs/
├── llm_screening_prompts/
├── cl_st1_ph1_melina.ipynb
├── cl_st1_ph1_melina_pipeline.md
├── select_now_files.py
├── find_now_sources_text_matches.py
├── organise_now_articles.py
└── llm_screening.py
```

The root repository also contains:

```text
README.md
LICENSE
docs/
cl_st1_ph1_melina_deprecated/
```

Deprecated scripts and earlier workflows are retained separately where relevant for traceability.

### Workflow Overview

Run the commands below from the phase directory:

```shell
cd cl_st1_ph1_melina
```

#### 1. Select NOW Articles by Seed Term

The first step filters raw NOW text files for articles containing the target seed term, currently centred on `gaza`.

```shell
python select_now_files.py \
    --input corpus/01_now_dataset_raw/02_now_text_raw \
    --output corpus/01_now_dataset/02_now_text
```

The current extraction process recursively scans the raw NOW text dataset, filters `.txt` files for whole-word, case-insensitive matches, and preserves the original directory structure in the output.

Execution details are recorded in:

```text
select_now_files.log
```

#### 2. Match NOW Sources and Article Files

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

#### 3. Organise NOW Articles

Matched articles are then organised into a structured corpus using the study date range and a Global North/South country classification document.

```shell
python organise_now_articles.py \
    --initial-date 2023-09-01 \
    --final-date 2026-09-15 \
    --global-north-south-classification docs/now_country_codes_north_south.md \
    --input-articles corpus/01_now_dataset/02_now_text \
    --output-articles corpus/02_now_organised
```

The organised corpus currently produces consolidated outputs such as:

```text
corpus/palestine_now.ndjson
corpus/palestine_now.tsv
corpus/palestine_now.xlsx
```

These files provide structured article-level data for later analysis and screening.

### LLM-Assisted Screening

The project includes an LLM screening stage to assess whether organised articles are relevant to the research focus.

Screening outputs are stored under:

```text
corpus/03_now_screened/
```

A current screening run directory is:

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
palestine_now_screened.ndjson
```

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

### Corpus Scope

The working corpus is built from NOW articles containing the `gaza` seed term and is organised for a study period beginning in September 2023. The corpus includes articles from multiple national source files and supports comparative analysis across country groupings such as Global North and Global South classifications.

Earlier sample documents from 2018 and later documents from 2024 show the kind of NOW article material handled by the workflow, including news reports, opinion pieces, syndicated content, and repeated wire-service material. These examples also illustrate the need for deduplication, source matching, metadata preservation, and relevance screening.

### Main Outputs

Important generated outputs include:

| Output                                   | Description                                       |
|------------------------------------------|---------------------------------------------------|
| `corpus/01_now_dataset/`                 | Filtered NOW files selected by seed-term matching |
| `corpus/02_now_organised/`               | Organised article corpus by date/source metadata  |
| `corpus/palestine_now.ndjson`            | Main manifest for downstream screening            |
| `corpus/palestine_now.tsv`               | Tabular export of the organised corpus            |
| `corpus/palestine_now.xlsx`              | Spreadsheet export of the organised corpus        |
| `corpus/03_now_screened/`                | LLM-screened article outputs                      |
| `llm_screening_summary.json`             | Summary of a screening run                        |
| `llm_screening_failures.ndjson`          | Failed screening items                            |
| `llm_screening_invalid_responses.ndjson` | Invalid or unparsable model responses             |

### Documentation

Additional workflow notes are maintained in the phase directory:

```text
cl_st1_ph1_melina_pipeline.md
select_now_files.md
find_now_sources_text_matches.md
organise_now_articles.md
llm_screening.md
```

These documents provide step-level details for the extraction, matching, organisation, and screening stages.

### Reproducibility Notes

- Commands should be run from `cl_st1_ph1_melina/`.
- Generated logs and manifests should be retained for auditability.
- LLM screening runs should use `--resume` when continuing an interrupted or partial run.
- Failed and invalid responses are written separately so they can be reviewed and retried.
- Timestamped screening manifests are preserved to document individual screening attempts.

### License

See `LICENSE`.
