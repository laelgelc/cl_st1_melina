# Corpus Linguistics - Study 1 - Melina

## Phase 1 - Data Collection and Sampling

This phase aims to explore the [NOW](https://www.english-corpora.org/corpora.asp) corpus and evaluate the feasibility of using it for this study.

### Data Extraction Progress

The script `select_now_files.py` was refactored to streamline the text extraction process. The previous archive extraction logic was removed (now preserved in `select_now_files_deprecated.py` for reference). The updated script now recursively processes the input dataset directory, filtering all `.txt` files for lines containing our target search terms (e.g., "gaza") as whole words, case-insensitive. Importantly, it preserves the original directory structure when writing the filtered text files to the output directory.

The execution of the refactored programme successfully processed thousands of text files. The detailed execution results, including the exact number of matching lines extracted per file and any skipped files, were registered and can be reviewed in the `select_now_files.log` file.
