# Corpus Linguistics - Study 1 - Phase 2 - Melina

Run the commands from the project phase directory, e.g.:

```text
cl_st1_ph2_melina/
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

global_north_2023_09   → selected 40/40 from 604 available POSKW lemmas
global_north_2023_10   → selected 40/40 from 506 available POSKW lemmas
global_north_2023_11   → selected 40/40 from 396 available POSKW lemmas
global_north_2023_12   → selected 40/40 from 386 available POSKW lemmas
global_north_2024_01   → selected 40/40 from 378 available POSKW lemmas
global_north_2024_02   → selected 40/40 from 388 available POSKW lemmas
global_north_2024_03   → selected 40/40 from 428 available POSKW lemmas
global_north_2024_04   → selected 40/40 from 453 available POSKW lemmas
global_north_2024_05   → selected 40/40 from 472 available POSKW lemmas
global_north_2024_06   → selected 40/40 from 351 available POSKW lemmas
global_north_2024_07   → selected 40/40 from 334 available POSKW lemmas
global_north_2024_08   → selected 40/40 from 360 available POSKW lemmas
global_north_2024_09   → selected 40/40 from 341 available POSKW lemmas
global_north_2024_10   → selected 40/40 from 401 available POSKW lemmas
global_north_2024_11   → selected 40/40 from 418 available POSKW lemmas
global_north_2024_12   → selected 40/40 from 364 available POSKW lemmas
global_north_2025_01   → selected 40/40 from 441 available POSKW lemmas
global_north_2025_02   → selected 40/40 from 475 available POSKW lemmas
global_north_2025_03   → selected 40/40 from 455 available POSKW lemmas
global_north_2025_04   → selected 40/40 from 413 available POSKW lemmas
global_north_2025_05   → selected 40/40 from 478 available POSKW lemmas
global_north_2025_06   → selected 40/40 from 528 available POSKW lemmas
global_south_2023_09   → selected 40/40 from 328 available POSKW lemmas
global_south_2023_10   → selected 40/40 from 444 available POSKW lemmas
global_south_2023_11   → selected 40/40 from 361 available POSKW lemmas
global_south_2023_12   → selected 40/40 from 438 available POSKW lemmas
global_south_2024_01   → selected 40/40 from 400 available POSKW lemmas
global_south_2024_02   → selected 40/40 from 288 available POSKW lemmas
global_south_2024_03   → selected 40/40 from 309 available POSKW lemmas
global_south_2024_04   → selected 40/40 from 322 available POSKW lemmas
global_south_2024_05   → selected 40/40 from 298 available POSKW lemmas
global_south_2024_06   → selected 40/40 from 268 available POSKW lemmas
global_south_2024_07   → selected 40/40 from 353 available POSKW lemmas
global_south_2024_08   → selected 40/40 from 402 available POSKW lemmas
global_south_2024_09   → selected 40/40 from 398 available POSKW lemmas
global_south_2024_10   → selected 40/40 from 466 available POSKW lemmas
global_south_2024_11   → selected 40/40 from 425 available POSKW lemmas
global_south_2024_12   → selected 40/40 from 343 available POSKW lemmas
global_south_2025_01   → selected 40/40 from 412 available POSKW lemmas
global_south_2025_02   → selected 40/40 from 464 available POSKW lemmas
global_south_2025_03   → selected 40/40 from 403 available POSKW lemmas
global_south_2025_04   → selected 40/40 from 313 available POSKW lemmas
global_south_2025_05   → selected 40/40 from 415 available POSKW lemmas
global_south_2025_06   → selected 40/40 from 461 available POSKW lemmas

Total consolidated keywords before de-duplication: 1760
Unique keywords after de-duplication: 1079
Duplicates removed: 681

Final unique keywords written to: corpus/07_kw_selected/keywords.txt
Final unique keyword count: 1079
```

