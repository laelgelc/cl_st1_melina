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

## 

```shell
python organise_now_articles.py \
    --initial-date 2023-09-01 \
    --final-date 2026-09-15 \
    --global-north-south-classification docs/now_country_codes_north_south.md \
    --input-articles corpus/01_now_dataset/02_now_text \
    --output-articles corpus/02_now_organised
```

Having the `find_now_sources_text_matches.py` programme as a reference, write the development specification for the `organise_now_articles.py` with the following syntax:

```shell
python organise_now_articles.py \
    --initial-date 2023-09-01 \
    --final-date 2026-09-15 \
    --global-north-south-classification docs/now_country_codes_north_south.md \
    --input-articles corpus/01_now_dataset/02_now_text \
    --output-articles corpus/02_now_organised
```

and with the following functionalities:

1. Parse the files in subdirectories that correspond to the period specified by `--initial-date` and `--final-date`. The subdirectories are formatted as follows:

```text
23-09-text
23-10-text
text-25-01
text-25-02
```

The Year and Month should be inferred from the subdirectory names. When the input parameters specify the Date but the subdirectories specify only Year and Month, then only the Year and Month in the parameters should be considered.

2. For the identified subdirectories, the article IDs should be fetched from all the files to detect duplicate article IDs. The article IDs should be extracted from the filenames, which are formatted as follows:

```text
@@101631126 <p> GAZA , - Israel will allow the export of commercial goods from the Gaza Strip through a main border crossing from Sunday after a days-long ban for 
```

The duplicate article IDs should be reported in a diagnostic file.

Throughout the processing, only the first article should be considered in the case of duplicate article IDs.

3. Malformed selected article lines should be reported in a diagnostic file and disconsidered.

4. The content of the article, which is the text after the article ID, should be transcribed into a file named after the article ID. The files should be organised in the `--output-articles` directory as subdirectories as follows:

```text
corpus/
├── 02_now_organised/
    ├── global_north_2023_09/
    │   ├── au/
    │   │   ├── 101631127.txt
    │   │   └── 101631128.txt
    │   ├── ca/       
    │   │   ├── 101631129.txt
    │   │   ├── 101631130.txt
    │   │   └── 101631131.txt
    │    
    ├── global_south_2023_09/
    │   ├── bd/
    │   │   ├── 101631127.txt
    │   │   └── 101631128.txt
    │   ├── gh/       
    │   │   ├── 101631129.txt
    │   │   ├── 101631130.txt
    │   │   └── 101631131.txt 
```

The organisation should be made according to the document specified in `--global-north-south-classification`.

The Year and Month should correspond to the subdirectory of origin

```text
23-09-text
23-10-text
text-25-01
text-25-02
```

The country code should be taken from the filename from which the article was extracted:

```text
23-09-gb.txt
23-09-ph.txt
```

Files like `21-07-us1.txt` / `21-07-us2.txt` -> captures "us"

Is it clear?