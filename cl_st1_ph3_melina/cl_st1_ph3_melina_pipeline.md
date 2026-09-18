# Corpus Linguistics - Study 1 - Phase 3 - Melina

Run the commands from the project phase directory, e.g.:

```text
cl_st1_ph3_melina/
```

## 1. Tag the corpus

```shell
python tag.py
```

Output: `corpus/05_tagged/<group>/`

## 2. Extract key lemmas by group

```shell
python keylemmas.py \
  --input corpus/05_tagged \
  --output corpus/06_keylemmas \
  --cutoff 3
```

Output: `corpus/06_keylemmas/<group>.tsv`

## 3. Select a stratified keyword set

```shell
python select_kws_stratified.py \
    --per-group 40 \
    --max-total 20000
```

Output: `corpus/07_kw_selected/keywords.txt

```shell
=== Group Keyword Quotas ===
global_north_2023_09   → 40 keywords max
global_north_2023_10   → 40 keywords max
global_north_2023_11   → 40 keywords max
global_north_2023_12   → 40 keywords max
global_north_2024_01   → 40 keywords max
global_north_2024_02   → 40 keywords max
global_north_2024_03   → 40 keywords max
global_north_2024_04   → 40 keywords max
global_north_2024_05   → 40 keywords max
global_north_2024_06   → 40 keywords max
global_north_2024_07   → 40 keywords max
global_north_2024_08   → 40 keywords max
global_north_2024_09   → 40 keywords max
global_north_2024_10   → 40 keywords max
global_north_2024_11   → 40 keywords max
global_north_2024_12   → 40 keywords max
global_north_2025_01   → 40 keywords max
global_north_2025_02   → 40 keywords max
global_north_2025_03   → 40 keywords max
global_north_2025_04   → 40 keywords max
global_north_2025_05   → 40 keywords max
global_north_2025_06   → 40 keywords max
global_south_2023_09   → 40 keywords max
global_south_2023_10   → 40 keywords max
global_south_2023_11   → 40 keywords max
global_south_2023_12   → 40 keywords max
global_south_2024_01   → 40 keywords max
global_south_2024_02   → 40 keywords max
global_south_2024_03   → 40 keywords max
global_south_2024_04   → 40 keywords max
global_south_2024_05   → 40 keywords max
global_south_2024_06   → 40 keywords max
global_south_2024_07   → 40 keywords max
global_south_2024_08   → 40 keywords max
global_south_2024_09   → 40 keywords max
global_south_2024_10   → 40 keywords max
global_south_2024_11   → 40 keywords max
global_south_2024_12   → 40 keywords max
global_south_2025_01   → 40 keywords max
global_south_2025_02   → 40 keywords max
global_south_2025_03   → 40 keywords max
global_south_2025_04   → 40 keywords max
global_south_2025_05   → 40 keywords max
global_south_2025_06   → 40 keywords max
============================

global_north_2023_09   → selected 40/40 from 459 available POSKW lemmas
global_north_2023_10   → selected 40/40 from 563 available POSKW lemmas
global_north_2023_11   → selected 40/40 from 435 available POSKW lemmas
global_north_2023_12   → selected 40/40 from 364 available POSKW lemmas
global_north_2024_01   → selected 40/40 from 312 available POSKW lemmas
global_north_2024_02   → selected 40/40 from 340 available POSKW lemmas
global_north_2024_03   → selected 40/40 from 382 available POSKW lemmas
global_north_2024_04   → selected 40/40 from 406 available POSKW lemmas
global_north_2024_05   → selected 40/40 from 452 available POSKW lemmas
global_north_2024_06   → selected 40/40 from 302 available POSKW lemmas
global_north_2024_07   → selected 40/40 from 290 available POSKW lemmas
global_north_2024_08   → selected 40/40 from 272 available POSKW lemmas
global_north_2024_09   → selected 40/40 from 275 available POSKW lemmas
global_north_2024_10   → selected 40/40 from 345 available POSKW lemmas
global_north_2024_11   → selected 40/40 from 377 available POSKW lemmas
global_north_2024_12   → selected 40/40 from 314 available POSKW lemmas
global_north_2025_01   → selected 40/40 from 430 available POSKW lemmas
global_north_2025_02   → selected 40/40 from 476 available POSKW lemmas
global_north_2025_03   → selected 40/40 from 449 available POSKW lemmas
global_north_2025_04   → selected 40/40 from 407 available POSKW lemmas
global_north_2025_05   → selected 40/40 from 485 available POSKW lemmas
global_north_2025_06   → selected 40/40 from 521 available POSKW lemmas
global_south_2023_09   → selected 40/40 from 252 available POSKW lemmas
global_south_2023_10   → selected 40/40 from 428 available POSKW lemmas
global_south_2023_11   → selected 40/40 from 304 available POSKW lemmas
global_south_2023_12   → selected 40/40 from 368 available POSKW lemmas
global_south_2024_01   → selected 40/40 from 339 available POSKW lemmas
global_south_2024_02   → selected 40/40 from 246 available POSKW lemmas
global_south_2024_03   → selected 40/40 from 266 available POSKW lemmas
global_south_2024_04   → selected 40/40 from 260 available POSKW lemmas
global_south_2024_05   → selected 40/40 from 263 available POSKW lemmas
global_south_2024_06   → selected 40/40 from 231 available POSKW lemmas
global_south_2024_07   → selected 40/40 from 291 available POSKW lemmas
global_south_2024_08   → selected 40/40 from 350 available POSKW lemmas
global_south_2024_09   → selected 40/40 from 340 available POSKW lemmas
global_south_2024_10   → selected 40/40 from 422 available POSKW lemmas
global_south_2024_11   → selected 40/40 from 368 available POSKW lemmas
global_south_2024_12   → selected 40/40 from 308 available POSKW lemmas
global_south_2025_01   → selected 40/40 from 348 available POSKW lemmas
global_south_2025_02   → selected 40/40 from 395 available POSKW lemmas
global_south_2025_03   → selected 40/40 from 341 available POSKW lemmas
global_south_2025_04   → selected 40/40 from 285 available POSKW lemmas
global_south_2025_05   → selected 40/40 from 371 available POSKW lemmas
global_south_2025_06   → selected 40/40 from 443 available POSKW lemmas

Total consolidated keywords before de-duplication: 1760
Unique keywords after de-duplication: 1012
Duplicates removed: 748

Final unique keywords written to: corpus/07_kw_selected/keywords.txt
Final unique keyword count: 1012
```

## 4. Build binary keyword columns

```shell
rm -rf columns columns_clean
```

```shell
python columns.py
```

Outputs:
- `columns/`
- `columns_clean/`
- `file_ids.txt`
- `index_keywords.txt`

## 5. Merge columns into the SAS counts matrix

```shell
python merge_columns.py
```

Output: `sas/counts.txt`

## 6. Generate SAS format files

```shell
python sas_formats.py
```

Outputs:

- sas/word_labels_format.sas
- sas/word_labels_full_format.sas
- other SAS helper format files

## 7. Run SAS

## 8. Build factor loading lists

```shell
python factor_lists.py
```

Output: factors/

## 9. Calculate corpus size summaries

```shell
python corpus_size.py
```

Output: `corpus_size/corpus_size.tsv`

## 10. Generate LaTeX/TikZ boxplots

```shell
cd latex_boxplots
```

```shell
python latex_boxplots.py
```

Output: `latex_boxplots/slides/`

```shell
cd ..
```

## 11. Generate LaTeX ANOVA table

```shell
python latex_anova_table.py
```

Output: `latex_tables/anova_decade.tex`

## 12. Generate LaTeX example extracts

```shell
python examples.py
```

Output: `examples/`

## 13. Generate score-details report

```shell
python score_details.py
```

Output: `examples/score_details.txt`

## 14. Generate plaintext example extracts

```shell
python examples_txt.py
```

Output: `examples_txt/`

## 15. Build interpretation prompts

```shell
python interpretation_prompts.py
```

Output: `interpretation/input/`

## 16. Submit interpretation prompts to GPT

```shell
python generate_interpretation_gpt.py \
    --input interpretation/input \
    --output interpretation/output \
    --model gpt-5.6-sol \
    --workers 4
```
Output: `interpretation/output/`
