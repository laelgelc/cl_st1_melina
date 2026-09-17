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
    --per-group 25 \
    --max-total 1200
```

Output: `corpus/07_kw_selected/keywords.txt

