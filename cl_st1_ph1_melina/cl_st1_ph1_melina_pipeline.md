# Corpus Linguistics - Study 1 - Phase 1 - Melina

Run the commands from the project phase directory, e.g.:

```text
cl_st1_ph1_melina/
```

## 1. Select NOW news articles the contain the `gaza` seed term

```shell
python select_now_files.py \
    --input corpus/01_now_dataset_raw/02_now_text_raw \
    --output corpus/01_now_dataset/02_now_text
```

## 2. Find NOW sources and news articles matches

```shell
python find_now_sources_text_matches.py \
    --initial-date 2020-01-01 \
    --final-date 2020-12-31 \
    --input-sources corpus/01_now_dataset_raw/01_now_sources_raw \
    --input-articles corpus/01_now_dataset/02_now_text \
    --match corpus/01_now_dataset/01_now_matched_sources_2020_test
```

```shell
python find_now_sources_text_matches.py \
    --initial-date 2023-09-01 \
    --final-date 2026-09-14 \
    --input-sources corpus/01_now_dataset_raw/01_now_sources_raw \
    --input-articles corpus/01_now_dataset/02_now_text \
    --match corpus/01_now_dataset/01_now_matched_sources_2023_2026_test
```

## Organise NOW articles

```shell
python organise_now_articles.py \
    --initial-date 2023-09-01 \
    --final-date 2026-09-15 \
    --global-north-south-classification docs/now_country_codes_north_south.md \
    --input-articles corpus/01_now_dataset/02_now_text \
    --output-articles corpus/02_now_organised
```

## LLM Screening

### Dry run

```shell
python llm_screening.py \
    --manifest corpus/palestine_now.ndjson \
    --output corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna \
    --prompt llm_screening_prompts/llm_screening_v2.md \
    --model gpt-5.6-luna \
    --limit 10 \
    --dry-run
```


### Test run, first time

```shell
python llm_screening.py \
    --manifest corpus/palestine_now.ndjson \
    --output corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna \
    --prompt llm_screening_prompts/llm_screening_v2.md \
    --model gpt-5.6-luna \
    --limit 10
```

### 20 workers test run

```shell
python llm_screening.py \
    --manifest corpus/palestine_now.ndjson \
    --output corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna \
    --prompt llm_screening_prompts/llm_screening_v2.md \
    --model gpt-5.6-luna \
    --limit 200 \
    --workers 20 \
    --resume
```

### Full run

```shell
python llm_screening.py \
    --manifest corpus/palestine_now.ndjson \
    --output corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna \
    --prompt llm_screening_prompts/llm_screening_v2.md \
    --model gpt-5.6-luna \
    --workers 10 \
    --resume
```

### Production mode on an EC2 instance

```shell
bash run_python_ec2.sh \
    llm_screening.py \
    --manifest corpus/palestine_now.ndjson \
    --output corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna \
    --prompt llm_screening_prompts/llm_screening_v2.md \
    --model gpt-5.6-luna \
    --workers 10 \
    --resume
```