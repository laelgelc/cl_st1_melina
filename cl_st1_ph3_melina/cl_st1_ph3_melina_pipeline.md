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

## Extract key lemmas by group

```shell
python keylemmas.py \
  --input corpus/05_tagged \
  --output corpus/06_keylemmas \
  --cutoff 3
```

# Output: `corpus/06_keylemmas/<group>.tsv`

