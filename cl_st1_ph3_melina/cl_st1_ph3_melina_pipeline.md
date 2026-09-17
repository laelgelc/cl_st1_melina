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

global_north_2023_09   → selected 40/40 from 611 available POSKW lemmas
global_north_2023_10   → selected 40/40 from 601 available POSKW lemmas
global_north_2023_11   → selected 40/40 from 480 available POSKW lemmas
global_north_2023_12   → selected 40/40 from 418 available POSKW lemmas
global_north_2024_01   → selected 40/40 from 374 available POSKW lemmas
global_north_2024_02   → selected 40/40 from 410 available POSKW lemmas
global_north_2024_03   → selected 40/40 from 437 available POSKW lemmas
global_north_2024_04   → selected 40/40 from 478 available POSKW lemmas
global_north_2024_05   → selected 40/40 from 511 available POSKW lemmas
global_north_2024_06   → selected 40/40 from 352 available POSKW lemmas
global_north_2024_07   → selected 40/40 from 334 available POSKW lemmas
global_north_2024_08   → selected 40/40 from 351 available POSKW lemmas
global_north_2024_09   → selected 40/40 from 328 available POSKW lemmas
global_north_2024_10   → selected 40/40 from 387 available POSKW lemmas
global_north_2024_11   → selected 40/40 from 443 available POSKW lemmas
global_north_2024_12   → selected 40/40 from 377 available POSKW lemmas
global_north_2025_01   → selected 40/40 from 495 available POSKW lemmas
global_north_2025_02   → selected 40/40 from 525 available POSKW lemmas
global_north_2025_03   → selected 40/40 from 491 available POSKW lemmas
global_north_2025_04   → selected 40/40 from 458 available POSKW lemmas
global_north_2025_05   → selected 40/40 from 534 available POSKW lemmas
global_north_2025_06   → selected 40/40 from 579 available POSKW lemmas
global_south_2023_09   → selected 40/40 from 331 available POSKW lemmas
global_south_2023_10   → selected 40/40 from 504 available POSKW lemmas
global_south_2023_11   → selected 40/40 from 362 available POSKW lemmas
global_south_2023_12   → selected 40/40 from 450 available POSKW lemmas
global_south_2024_01   → selected 40/40 from 421 available POSKW lemmas
global_south_2024_02   → selected 40/40 from 304 available POSKW lemmas
global_south_2024_03   → selected 40/40 from 318 available POSKW lemmas
global_south_2024_04   → selected 40/40 from 343 available POSKW lemmas
global_south_2024_05   → selected 40/40 from 320 available POSKW lemmas
global_south_2024_06   → selected 40/40 from 281 available POSKW lemmas
global_south_2024_07   → selected 40/40 from 378 available POSKW lemmas
global_south_2024_08   → selected 40/40 from 422 available POSKW lemmas
global_south_2024_09   → selected 40/40 from 412 available POSKW lemmas
global_south_2024_10   → selected 40/40 from 478 available POSKW lemmas
global_south_2024_11   → selected 40/40 from 450 available POSKW lemmas
global_south_2024_12   → selected 40/40 from 363 available POSKW lemmas
global_south_2025_01   → selected 40/40 from 415 available POSKW lemmas
global_south_2025_02   → selected 40/40 from 470 available POSKW lemmas
global_south_2025_03   → selected 40/40 from 415 available POSKW lemmas
global_south_2025_04   → selected 40/40 from 325 available POSKW lemmas
global_south_2025_05   → selected 40/40 from 422 available POSKW lemmas
global_south_2025_06   → selected 40/40 from 472 available POSKW lemmas

Total consolidated keywords before de-duplication: 1760
Unique keywords after de-duplication: 1056
Duplicates removed: 704

Final unique keywords written to: corpus/07_kw_selected/keywords.txt
Final unique keyword count: 1056
```

