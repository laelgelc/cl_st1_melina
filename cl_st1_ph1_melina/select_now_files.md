# Development Specification: `select_now_files.py`

Write a Python programme named `select_now_files.py` that processes a dataset directory and writes filtered outputs to another directory.

## Purpose

The script scans an input directory and its subdirectories, and filters `.txt` files by matching lines that contain any configured search term as a whole word, case-insensitive. Matching lines are written to same-named output files in their corresponding subdirectories in the output directory.

## Command-line interface

Accept the following command-line arguments:

- `--input`: path to the input directory
- `--output`: path to the output directory

## Functional requirements

### Directory handling

- Create the output directory if it does not exist.
- Use clear, robust code with basic error handling.
- Create a log file named `select_now_files.log` in the same directory where `select_now_files_deprecated.py` is located.
- Log to both the console and the log file.
- Use standard log levels such as `INFO`, `WARNING`, and `ERROR`.

### Text processing

- Process all `.txt` files in the input directory and its subdirectories.
- Read each text file line by line.
- Keep only lines where any term in a Python list appears as a whole word, case-insensitive.
- The term list must contain `gaza`, but may include more terms later.
- The selection logic must use OR behaviour across the list items.
- If a `.txt` file has at least one matching line, write an output file with the same filename to the same subdirectory in the output directory containing only those matching lines.
- If a `.txt` file has no matching lines, do not create an output file for it.
- Write output files with LF line endings.

## Documentation requirement

- Place a docstring at the top of the programme explaining:
  - what the script does
  - how to use it

## Logging requirements

- Log file processing results, including whether a matching output file was written or skipped due to no matches.
- Log any recoverable errors and continue processing where appropriate.

## Implementation notes

- The matching logic should treat each search term as a whole word.
- Matching must be case-insensitive.
- The script should be structured so that the term list can be expanded easily in the future.