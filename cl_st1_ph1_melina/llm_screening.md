# Development Specification: `llm_screening.py`

## 1. Programme purpose

`llm_screening.py` screens NOW corpus news articles with a GPT model to classify their relevance for a corpus-linguistics research project studying media discourses around Gaza, Palestine, Israel/Palestine, and the Palestinian conflict between 2023 and 2025.

The programme takes an immutable NDJSON article manifest as input. Each manifest row identifies one article and includes the path to the corresponding article text file. For each article, the programme:

1. reads the article metadata from the manifest;
2. reads the article text from the manifest row’s `filepath`;
3. renders an LLM screening prompt by inserting the article text;
4. submits the prompt to the OpenAI API;
5. parses and validates the JSON response;
6. saves one per-article JSON screening artefact;
7. writes run-level manifests and logs;
8. produces a consolidated screened NDJSON dataset.

The programme is intended for large-scale screening of approximately 117,000+ articles. It must therefore support:

- resumable execution;
- robust per-article failure handling;
- concurrent workers;
- immutable input data;
- reproducible run metadata;
- prompt version tracking;
- API usage tracking where available;
- safe handling of API credentials.

---

## 2. Research context

The article dataset was initially extracted from the NOW corpus using the seed term `gaza`. The seed-term extraction produced a broad candidate corpus, but not every article that contains `gaza` is substantively relevant to the research.

The screening task is to classify each candidate article into one of three research-use categories:

| Category     | Meaning                                                                                                                                                                                                                                                                      |
|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `CORE`       | The article is centrally or substantially about Gaza, Palestine, Israel/Palestine, the Israel-Hamas war, occupation, blockade, humanitarian conditions, diplomacy, protests, media framing, international law, or other directly connected conflict issues.                  |
| `PERIPHERAL` | The article is mainly about another subject but contains meaningful discourse related to Gaza, Palestine, Israel/Palestine, Zionism, antisemitism, Islamophobia, colonialism, terrorism, humanitarianism, international law, protests, or public debate around the conflict. |
| `EXCLUDE`    | The article contains only an incidental, boilerplate, unrelated, navigational, metadata, roundup, comment-section, or passing mention of Gaza/Palestine/Israel-Palestine.                                                                                                    |

The programme must not perform discourse analysis itself. It only performs screening/classification for downstream corpus construction and analysis.

---

## 3. Core design principles

### 3.1 Immutable input

The input manifest must not be modified in place.

The programme must treat:

```
corpus/palestine_now.ndjson
```


as an immutable source manifest.

All screening outcomes must be written to a separate output directory.

---

### 3.2 Manifest-driven processing

The programme must be driven by an NDJSON manifest, not by recursively scanning an article directory.

Each manifest row represents one intended article to screen.

Required manifest fields:

```json
{
  "article_id": "101549943",
  "group": "global_north_2023_09",
  "country_code": "ie",
  "filepath": "corpus/02_now_organised/global_north_2023_09/ie/101549943.txt"
}
```


At minimum, the programme requires:

| Field          |    Required | Purpose                                        |
|----------------|------------:|------------------------------------------------|
| `article_id`   |         Yes | Stable unique identifier for the article       |
| `filepath`     |         Yes | Path to the article text file                  |
| `group`        | Recommended | Grouping variable, e.g. `global_north_2023_09` |
| `country_code` | Recommended | Country/source code                            |

If optional fields are present, they must be preserved in the output.

---

### 3.3 Per-article artefacts

Each article should produce one per-article JSON output file.

This supports:

- robust resume;
- parallel processing;
- per-article auditability;
- recovery from partial failures;
- invalid response inspection;
- reprocessing selected articles only.

Recommended per-article output path pattern:

```
<output>/screening_json/<group>/<country_code>/<article_id>.json
```


Example:

```
corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna/screening_json/global_north_2023_09/ie/101549943.json
```


If `group` or `country_code` is missing, the programme may use fallback directory names such as:

```
unknown_group
unknown_country
```


---

### 3.4 Consolidated screened dataset

In addition to per-article JSON files, the programme must produce a consolidated NDJSON file.

Recommended path:

```
<output>/palestine_now_screened.ndjson
```


This file should contain one successfully screened article per line, preserving the original manifest row and adding the LLM screening result.

---

### 3.5 File-based resume

Resume must be based on existing successful per-article JSON artefacts, not on a “last processed article” pointer.

For each manifest row:

```
if --resume is enabled
and expected per-article JSON exists
and status == "success":
    skip article
else:
    process article
```


This is necessary because concurrent workers may complete articles out of manifest order.

---

### 3.6 Reproducibility

The programme must record enough information to reproduce or audit a run:

- input manifest path;
- input manifest hash;
- article file path;
- article text hash;
- prompt file path;
- prompt template hash;
- rendered prompt hash;
- selected model;
- model response metadata where available;
- token usage where available;
- timestamp;
- duration;
- screening output;
- error information;
- run ID;
- worker configuration;
- retry configuration;
- dry-run/resume/reprocess status.

---

## 4. Command-line interface

### 4.1 Recommended commands

#### Dry run

```textmate
python llm_screening.py \
    --manifest corpus/palestine_now.ndjson \
    --output corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna \
    --prompt llm_screening_prompts/llm_screening_v2.md \
    --model gpt-5.6-luna \
    --limit 10 \
    --dry-run
```


#### Test run

```textmate
python llm_screening.py \
    --manifest corpus/palestine_now.ndjson \
    --output corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna \
    --prompt llm_screening_prompts/llm_screening_v2.md \
    --model gpt-5.6-luna \
    --limit 10 \
    --resume
```


#### Full run

```textmate
python llm_screening.py \
    --manifest corpus/palestine_now.ndjson \
    --output corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna \
    --prompt llm_screening_prompts/llm_screening_v2.md \
    --model gpt-5.6-luna \
    --workers 10 \
    --resume
```


#### Production mode on an EC2 instance

```textmate
bash run_python_ec2.sh \
    llm_screening.py \
    --manifest corpus/palestine_now.ndjson \
    --output corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna \
    --prompt llm_screening_prompts/llm_screening_v2.md \
    --model gpt-5.6-luna \
    --workers 10 \
    --resume
```


---

### 4.2 Required arguments

| Argument          | Required | Description                            |
|-------------------|---------:|----------------------------------------|
| `--manifest PATH` |      Yes | Input NDJSON article manifest          |
| `--output PATH`   |      Yes | Output directory for screening results |
| `--prompt PATH`   |      Yes | Markdown prompt template file          |
| `--model MODEL`   |      Yes | GPT model ID used for screening        |

---

### 4.3 Optional arguments

| Argument                        |                                Default | Description                                                     |
|---------------------------------|---------------------------------------:|-----------------------------------------------------------------|
| `--limit N`                     |                                 `None` | Process only the first `N` planned articles                     |
| `--resume`                      |                                `False` | Skip existing successful per-article outputs                    |
| `--reprocess`                   |                                `False` | Reprocess even if successful per-article outputs already exist  |
| `--dry-run`                     |                                `False` | Validate inputs and build planned prompts without API calls     |
| `--workers N`                   |                                    `1` | Number of concurrent worker threads                             |
| `--max-retries N`               |                                    `2` | Number of retries per API call after the initial attempt        |
| `--retry-backoff-seconds FLOAT` |                                  `5.0` | Initial retry backoff in seconds                                |
| `--temperature FLOAT`           |                                  `0.0` | Temperature if supported by the selected model                  |
| `--max-output-tokens N`         |                                  `500` | Maximum output tokens for classification response, if supported |
| `--env-file PATH`               |                             `env/.env` | Optional environment file containing API credentials            |
| `--log-file PATH`               |           `<output>/llm_screening.log` | Optional explicit log file                                      |
| `--manifest-file PATH`          | `<output>/llm_screening_manifest.json` | Optional explicit run manifest file                             |
| `--article-id-field FIELD`      |                           `article_id` | Manifest field containing article ID                            |
| `--filepath-field FIELD`        |                             `filepath` | Manifest field containing article text path                     |
| `--group-field FIELD`           |                                `group` | Manifest field containing group                                 |
| `--country-code-field FIELD`    |                         `country_code` | Manifest field containing country code                          |

---

### 4.4 Argument validation

The programme must fail before any API call if:

- `--manifest` is missing;
- `--manifest` does not exist;
- `--manifest` is not a file;
- `--prompt` is missing;
- `--prompt` does not exist;
- `--prompt` is empty;
- `--output` cannot be created;
- `--model` is empty;
- `--limit <= 0`, if supplied;
- `--workers <= 0`;
- `--max-retries < 0`;
- `--retry-backoff-seconds < 0`;
- `--temperature < 0`;
- the OpenAI Python SDK is unavailable when not in dry-run mode;
- `OPENAI_API_KEY` is unavailable when not in dry-run mode.

The programme should not fail solely because `--env-file` does not exist, provided `OPENAI_API_KEY` is already available in the process environment.

---

## 5. Input manifest

### 5.1 Format

The manifest must be NDJSON: one JSON object per line.

Example:

```json
{"article_id":"101549943","group":"global_north_2023_09","country_code":"ie","filepath":"corpus/02_now_organised/global_north_2023_09/ie/101549943.txt"}
```


Each non-empty line must parse as a JSON object.

---

### 5.2 Required manifest fields

Each row must contain:

```
article_id
filepath
```


or the corresponding fields specified by:

```
--article-id-field
--filepath-field
```


If a row lacks required fields, that row should be recorded as a per-row failure, but the programme should continue processing other rows.

---

### 5.3 Manifest row preservation

The programme must preserve the original manifest row in per-article JSON and consolidated NDJSON output.

This allows later analysis by any original metadata fields.

---

### 5.4 Manifest loading strategy

The programme may either:

1. stream manifest rows line by line; or
2. load all rows into memory.

Given approximately 117,000 articles, loading the manifest into memory is acceptable if implementation is simpler. However, the article texts themselves must not be loaded all at once.

Recommended approach:

- read all manifest rows once for validation/planning;
- preserve original row order;
- process article texts individually.

---

## 6. Prompt template

### 6.1 Prompt file

The programme must load the screening prompt from the path given by:

```
--prompt
```


Example:

```
llm_screening_prompts/llm_screening_v2.md
```


The prompt must be external to the programme. Prompt contents must not be hardcoded.

---

### 6.2 Article placeholder

The prompt template must contain:

```
<<<ARTICLE_TEXT>>>
```


For each article, the programme must replace this placeholder with the article text.

If the prompt does not contain this placeholder, the programme must fail before API calls.

---

### 6.3 Recommended prompt ending

The prompt should contain a section similar to:

```
Article text:

<article>
<<<ARTICLE_TEXT>>>
</article>
```


The programme should not add Markdown code fences around the article text.

---

### 6.4 Prompt hashing

The programme must compute and record:

```
prompt_template_sha256
rendered_prompt_sha256
```


The rendered prompt hash should be computed after inserting the article text.

---

## 7. Article text handling

### 7.1 File path resolution

The article `filepath` from the manifest may be:

- relative; or
- absolute.

Relative paths should be resolved against the directory containing `llm_screening.py` or against the current working directory, depending on the project’s path convention.

Recommended behaviour for this project:

```
Relative CLI paths and manifest filepaths are resolved against the directory containing llm_screening.py.
```


This matches the style of project-situated scripts and makes execution portable across working directories.

---

### 7.2 Article file reading

Article files must be read as UTF-8 text using:

```
encoding="utf-8"
errors="replace"
```


This prevents occasional encoding issues from crashing the full run.

---

### 7.3 Empty article files

If an article file is empty or contains only whitespace:

- mark that article as failed;
- write a per-article JSON failure artefact where possible;
- continue processing other articles.

---

### 7.4 Missing article files

If an article file does not exist:

- mark that article as failed;
- write a per-article JSON failure artefact;
- include the original manifest row;
- continue processing other articles.

---

### 7.5 Article text hashing

For each successfully read article, record:

```
article_text_sha256
```


---

## 8. LLM request construction

For each article, the programme should construct the request as:

```
[prompt template with <<<ARTICLE_TEXT>>> replaced by article text]
```


The programme may optionally add neutral metadata in a future version, but the first version should use the prompt template as the source of all instructions and only replace the article placeholder.

The LLM call must be stateless. It must not reuse prior conversational context between articles.

---

## 9. OpenAI API handling

### 9.1 Client creation

The programme should use the OpenAI Python SDK.

It must fail before API calls if the SDK is unavailable.

---

### 9.2 API key loading

The programme should load environment variables from:

```
--env-file
```


if it exists.

Recommended behaviour:

1. If `--env-file` exists, load simple `KEY=VALUE` lines.
2. Do not overwrite existing environment variables.
3. Check for `OPENAI_API_KEY`.
4. If not found and not in dry-run mode, fail before API calls.
5. Never log or write the API key value.

---

### 9.3 Safe environment metadata

The programme should record only safe metadata:

```json
{
  "environment": {
    "env_file": "env/.env",
    "env_file_found": true,
    "openai_api_key_available": true,
    "openai_api_key_source": "env_file_or_process_environment",
    "openai_api_key_logged": false
  }
}
```


The API key value must never appear in:

- logs;
- manifests;
- per-article JSON;
- errors;
- console output.

---

### 9.4 API response text extraction

The programme must robustly extract output text from the API response.

It should support at least:

- `response.output_text`;
- text content nested under response output items, where applicable.

If no usable text is found:

- mark the article as failed;
- record error type `empty_llm_response`;
- continue processing.

---

### 9.5 Retry logic

Each API call should be retried on recoverable errors.

Recommended parameters:

```
--max-retries 2
--retry-backoff-seconds 5.0
```


Backoff strategy:

```
sleep = retry_backoff_seconds * (2 ** attempt_number)
```


The programme should log retry attempts without logging full prompt content.

---

### 9.6 Temperature support

Some models may not support `temperature`.

The programme should:

1. attempt to send `temperature` if configured;
2. if the API rejects `temperature` as unsupported:
   - retry without `temperature`;
   - remember that this model does not support temperature for the rest of the run;
   - avoid sending `temperature` again for that model;
   - record whether temperature was sent.

This temperature-support cache must be thread-safe.

---

### 9.7 Token usage

If token usage metadata is available from the API response, record it in:

- per-article JSON;
- run manifest aggregate totals, if feasible.

Example:

```json
"usage": {
  "input_tokens": 1500,
  "output_tokens": 120,
  "total_tokens": 1620
}
```


---

## 10. LLM response validation

### 10.1 Expected response

The LLM is expected to return valid JSON only.

Expected screening object:

```json
{
  "category": "CORE",
  "confidence": 0.92,
  "gaza_role": "central",
  "main_topic": "Israeli military operations and humanitarian conditions in Gaza",
  "conflict_relevance": "The article centrally discusses Gaza, Hamas, civilian casualties, displacement, and international pressure.",
  "reason": "The article is centrally about the war in Gaza and its humanitarian and military dimensions.",
  "multi_article_or_snippet_issue": false,
  "recommended_for_main_corpus": true
}
```


---

### 10.2 Required response fields

The parsed JSON must contain:

| Field                            | Type    | Allowed values                                                                |
|----------------------------------|---------|-------------------------------------------------------------------------------|
| `category`                       | string  | `CORE`, `PERIPHERAL`, `EXCLUDE`                                               |
| `confidence`                     | number  | `0.0` to `1.0`                                                                |
| `gaza_role`                      | string  | `central`, `substantial`, `background`, `passing`, `boilerplate_or_unrelated` |
| `main_topic`                     | string  | non-empty recommended                                                         |
| `conflict_relevance`             | string  | non-empty recommended                                                         |
| `reason`                         | string  | non-empty recommended                                                         |
| `multi_article_or_snippet_issue` | boolean | `true` or `false`                                                             |
| `recommended_for_main_corpus`    | boolean | `true` or `false`                                                             |

---

### 10.3 Validation rules

The programme must validate:

- response is parseable JSON;
- response is a JSON object;
- required fields are present;
- `category` is one of the allowed values;
- `confidence` is numeric and between `0.0` and `1.0`;
- `gaza_role` is one of the allowed values;
- `multi_article_or_snippet_issue` is boolean;
- `recommended_for_main_corpus` is boolean.

Recommended consistency check:

```
recommended_for_main_corpus must be true only when category == CORE.
```


If this consistency check fails, either:

1. mark response invalid; or
2. correct `recommended_for_main_corpus` deterministically and record a warning.

Recommended first-version behaviour:

```
Mark response invalid rather than silently correcting it.
```


---

### 10.4 Invalid responses

If the model returns invalid JSON or fails schema validation:

- save a per-article JSON artefact with status `invalid_response`;
- include raw response text;
- include validation error;
- write to `llm_screening_invalid_responses.ndjson`;
- continue processing.

---

## 11. Output directory structure

Given:

```
--output corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna
```


the programme should create:

```
corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna/
  screening_json/
  llm_screening_manifest.json
  llm_screening_manifest_<RUN_ID>.json
  llm_screening.log
  palestine_now_screened.ndjson
  llm_screening_failures.ndjson
  llm_screening_invalid_responses.ndjson
  llm_screening_summary.json
```


---

## 12. Per-article JSON output

### 12.1 Successful article structure

Example:

```json
{
  "article_id": "101549943",
  "status": "success",
  "input": {
    "manifest_file": "corpus/palestine_now.ndjson",
    "article_file": "corpus/02_now_organised/global_north_2023_09/ie/101549943.txt",
    "prompt_file": "llm_screening_prompts/llm_screening_v2.md"
  },
  "manifest_row": {
    "article_id": "101549943",
    "group": "global_north_2023_09",
    "country_code": "ie",
    "filepath": "corpus/02_now_organised/global_north_2023_09/ie/101549943.txt"
  },
  "screening": {
    "category": "PERIPHERAL",
    "confidence": 0.78,
    "gaza_role": "background",
    "main_topic": "Book review of Naomi Klein's Doppelganger and online conspiracy culture",
    "conflict_relevance": "The article contains a limited but meaningful passage on Gaza, Israel, Zionism, and backlash after criticism of Israel.",
    "reason": "The article is mainly a book review but includes meaningful conflict-related discourse.",
    "multi_article_or_snippet_issue": false,
    "recommended_for_main_corpus": false
  },
  "model": {
    "configured_model": "gpt-5.6-luna",
    "response_model": "gpt-5.6-luna"
  },
  "hashes": {
    "manifest_file_sha256": "...",
    "article_text_sha256": "...",
    "prompt_template_sha256": "...",
    "rendered_prompt_sha256": "...",
    "raw_response_text_sha256": "..."
  },
  "api_metadata": {
    "id": "...",
    "model": "gpt-5.6-luna",
    "usage": {}
  },
  "raw_response_text": "{...}",
  "temperature": 0.0,
  "temperature_sent_to_api": true,
  "created_at": "2026-09-15T00:00:00Z",
  "duration_seconds": 1.24,
  "error": null
}
```


---

### 12.2 Failed article structure

Example:

```json
{
  "article_id": "102151649",
  "status": "failed",
  "input": {
    "manifest_file": "corpus/palestine_now.ndjson",
    "article_file": "corpus/02_now_organised/global_north_2023_09/au/102151649.txt",
    "prompt_file": "llm_screening_prompts/llm_screening_v2.md"
  },
  "manifest_row": {
    "article_id": "102151649",
    "group": "global_north_2023_09",
    "country_code": "au",
    "filepath": "corpus/02_now_organised/global_north_2023_09/au/102151649.txt"
  },
  "error_type": "missing_article_file",
  "error": "Article file not found",
  "created_at": "2026-09-15T00:00:00Z",
  "duration_seconds": 0.01
}
```


---

### 12.3 Invalid response structure

Example:

```json
{
  "article_id": "102151649",
  "status": "invalid_response",
  "input": {
    "manifest_file": "corpus/palestine_now.ndjson",
    "article_file": "corpus/02_now_organised/global_north_2023_09/au/102151649.txt",
    "prompt_file": "llm_screening_prompts/llm_screening_v2.md"
  },
  "manifest_row": {
    "article_id": "102151649",
    "group": "global_north_2023_09",
    "country_code": "au",
    "filepath": "corpus/02_now_organised/global_north_2023_09/au/102151649.txt"
  },
  "raw_response_text": "The article is relevant because...",
  "validation_error": "Response is not valid JSON",
  "api_metadata": {
    "id": "...",
    "usage": {}
  },
  "created_at": "2026-09-15T00:00:00Z",
  "duration_seconds": 1.02
}
```


---

## 13. Consolidated screened NDJSON

The programme must write:

```
<output>/palestine_now_screened.ndjson
```


This file should be generated deterministically in the same order as the input manifest.

Each line should contain:

- all fields from the original manifest row;
- `llm_screening`;
- `llm_screening_metadata`.

Example:

```json
{
  "article_id": "101549943",
  "group": "global_north_2023_09",
  "country_code": "ie",
  "filepath": "corpus/02_now_organised/global_north_2023_09/ie/101549943.txt",
  "llm_screening": {
    "category": "PERIPHERAL",
    "confidence": 0.78,
    "gaza_role": "background",
    "main_topic": "Book review of Naomi Klein's Doppelganger and online conspiracy culture",
    "conflict_relevance": "The article contains a limited but meaningful passage on Gaza, Israel, Zionism, and backlash after criticism of Israel.",
    "reason": "The article is mainly a book review but includes meaningful conflict-related discourse.",
    "multi_article_or_snippet_issue": false,
    "recommended_for_main_corpus": false
  },
  "llm_screening_metadata": {
    "status": "success",
    "model": "gpt-5.6-luna",
    "prompt_file": "llm_screening_prompts/llm_screening_v2.md",
    "prompt_template_sha256": "...",
    "screened_at": "2026-09-15T00:00:00Z",
    "per_article_json": "corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna/screening_json/global_north_2023_09/ie/101549943.json",
    "usage": {}
  }
}
```


Only successful screenings should be included in this file unless a future option explicitly includes failed records.

---

## 14. Failure and invalid-response NDJSON files

### 14.1 Failures

The programme must write:

```
<output>/llm_screening_failures.ndjson
```


Each line should correspond to one article-level failure, such as:

- missing article file;
- unreadable article file;
- empty article file;
- API error after retries;
- no usable LLM response text;
- output write failure.

---

### 14.2 Invalid responses

The programme must write:

```
<output>/llm_screening_invalid_responses.ndjson
```


Each line should correspond to one API response that was received but could not be parsed or validated.

---

## 15. Run manifest

### 15.1 Manifest files

The programme must write two run manifests:

```
<output>/llm_screening_manifest.json
<output>/llm_screening_manifest_<RUN_ID>.json
```


The first is the latest run manifest. The second is timestamped/ID-specific and should not be overwritten by later runs.

---

### 15.2 Run manifest content

The run manifest should include:

```json
{
  "run_id": "...",
  "programme": "llm_screening.py",
  "start_time": "2026-09-15T00:00:00Z",
  "end_time": "2026-09-15T01:00:00Z",
  "status": "success",
  "paths": {
    "manifest": "corpus/palestine_now.ndjson",
    "output": "corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna",
    "prompt": "llm_screening_prompts/llm_screening_v2.md",
    "log_file": "...",
    "screened_ndjson": "...",
    "failures_ndjson": "...",
    "invalid_responses_ndjson": "..."
  },
  "environment": {
    "env_file": "env/.env",
    "env_file_found": true,
    "openai_api_key_available": true,
    "openai_api_key_source": "env_file_or_process_environment",
    "openai_api_key_logged": false
  },
  "model_configuration": {
    "model": "gpt-5.6-luna",
    "temperature": 0.0,
    "max_output_tokens": 500
  },
  "processing": {
    "workers": 10,
    "limit": null,
    "resume": true,
    "reprocess": false,
    "dry_run": false,
    "max_retries": 2,
    "retry_backoff_seconds": 5.0
  },
  "hashes": {
    "manifest_file_sha256": "...",
    "prompt_template_sha256": "..."
  },
  "counts": {
    "manifest_rows_total": 117519,
    "articles_planned": 117519,
    "articles_succeeded": 100000,
    "articles_failed": 100,
    "articles_invalid_response": 10,
    "articles_skipped_existing": 17409,
    "category_core": 0,
    "category_peripheral": 0,
    "category_exclude": 0
  },
  "usage_totals": {
    "input_tokens": 0,
    "output_tokens": 0,
    "total_tokens": 0
  },
  "articles": [
    {
      "article_id": "101549943",
      "status": "success",
      "category": "PERIPHERAL",
      "per_article_json": "..."
    }
  ]
}
```


For very large runs, the `articles` list may be large but acceptable. If it becomes unwieldy, a future version may write a separate run index NDJSON.

---

## 16. Summary file

The programme should write:

```
<output>/llm_screening_summary.json
```


This file should contain a compact machine-readable summary:

```json
{
  "run_id": "...",
  "model": "gpt-5.6-luna",
  "prompt": "llm_screening_prompts/llm_screening_v2.md",
  "manifest": "corpus/palestine_now.ndjson",
  "screened_ndjson": "corpus/03_now_screened/llm_screening_v2_gpt-5.6-luna/palestine_now_screened.ndjson",
  "counts": {
    "manifest_rows_total": 117519,
    "articles_succeeded": 100000,
    "articles_failed": 100,
    "articles_invalid_response": 10,
    "articles_skipped_existing": 17409,
    "category_core": 70000,
    "category_peripheral": 15000,
    "category_exclude": 15000
  },
  "usage_totals": {
    "input_tokens": 0,
    "output_tokens": 0,
    "total_tokens": 0
  }
}
```


---

## 17. Logging

The programme must write a log file:

```
<output>/llm_screening.log
```


It should also log to console.

---

### 17.1 Required log information

The log should include:

- programme start;
- run ID;
- resolved manifest path;
- resolved output path;
- resolved prompt path;
- selected model;
- workers;
- dry-run status;
- resume status;
- reprocess status;
- limit, if supplied;
- prompt hash;
- manifest hash;
- number of manifest rows;
- number of planned articles;
- per-article start and finish at reasonable verbosity;
- skipped articles;
- failures;
- invalid responses;
- retry attempts;
- temperature unsupported warnings;
- final category counts;
- final success/failure counts;
- programme completion.

---

### 17.2 Sensitive data exclusion

The log must not include:

- `OPENAI_API_KEY`;
- authentication headers;
- full request payloads;
- full article text;
- full prompt text with article content.

It may log:

- hashes;
- article IDs;
- file paths;
- status;
- durations;
- error messages;
- safe API metadata.

---

## 18. Dry-run mode

When `--dry-run` is supplied, the programme must:

- validate CLI arguments;
- load environment metadata, but not require `OPENAI_API_KEY`;
- load and validate the prompt;
- confirm the article placeholder exists;
- load and validate the manifest;
- resolve planned article file paths;
- check whether article files exist;
- read article files if feasible;
- compute hashes and approximate prompt sizes;
- create output directories;
- write dry-run manifest/log/summary;
- make no API calls;
- write no successful screening classifications.

Dry-run mode is intended to catch file, path, manifest, and prompt issues before spending API budget.

---

## 19. Resume and reprocess behaviour

### 19.1 `--resume`

If `--resume` is supplied:

- skip any article whose expected per-article JSON exists and has `status == "success"`;
- count it as `articles_skipped_existing`;
- include skipped records in the run manifest.

---

### 19.2 `--reprocess`

If `--reprocess` is supplied:

- ignore existing per-article success files;
- call the API again;
- overwrite or replace per-article JSON outputs.

Recommended behaviour:

- if both `--resume` and `--reprocess` are supplied, `--reprocess` takes precedence;
- log a warning that existing successful outputs will be reprocessed.

---

### 19.3 Partial failures

Existing failed or invalid-response files should not be skipped by `--resume`.

They should be retried unless a future option such as `--skip-failed` is introduced.

---

## 20. Concurrent execution

### 20.1 Workers

The programme should support concurrent processing with:

```
--workers N
```


Use a thread pool because the workload is I/O-bound and API-bound.

---

### 20.2 Per-article file safety

Each worker writes only its own per-article JSON output file.

Workers should not concurrently append to the consolidated NDJSON.

Recommended approach:

1. workers produce per-article JSON files;
2. main thread collects results;
3. main thread writes consolidated NDJSON at the end in manifest order.

---

### 20.3 Shared state safety

Any shared state must be thread-safe, including:

- temperature unsupported model cache;
- counters, if updated during processing;
- logging is acceptable through Python logging.

---

## 21. Processing order

High-level processing order:

```
1. Parse CLI arguments.
2. Resolve paths.
3. Create output directories.
4. Configure logging.
5. Create run ID.
6. Load .env file if present.
7. Check API key unless dry-run.
8. Validate options.
9. Load prompt template.
10. Confirm <<<ARTICLE_TEXT>>> placeholder exists.
11. Compute prompt hash.
12. Load manifest rows.
13. Validate manifest rows.
14. Compute manifest hash.
15. Apply --limit if supplied.
16. Determine expected per-article output path for each row.
17. If --resume, skip existing successful outputs.
18. If --dry-run, write dry-run manifest and exit.
19. Initialise OpenAI client.
20. Process articles with configured workers:
    - read article text;
    - render prompt;
    - call API with retries;
    - extract response text;
    - parse JSON;
    - validate schema;
    - write per-article JSON;
    - return status.
21. Write failures NDJSON.
22. Write invalid responses NDJSON.
23. Write consolidated screened NDJSON in manifest order.
24. Write summary JSON.
25. Write run manifests.
26. Log final counts.
27. Exit.
```


---

## 22. Exit codes

Recommended exit behaviour:

| Condition                                                        | Exit code |
|------------------------------------------------------------------|----------:|
| All planned articles succeeded or were skipped successfully      |       `0` |
| Some articles failed or had invalid responses, but run completed |       `1` |
| Fatal setup error before processing                              |       `1` |
| Keyboard interruption                                            |     `130` |

A run with article-level failures should still write manifests and logs where possible.

---

## 23. Error handling

### 23.1 Fatal errors

The programme should stop before processing if:

- required CLI arguments are invalid;
- output directory cannot be created;
- prompt file is missing or invalid;
- prompt placeholder is missing;
- manifest file is missing or invalid globally;
- API key is missing outside dry-run mode;
- OpenAI SDK is missing outside dry-run mode.

---

### 23.2 Per-article recoverable errors

The programme should mark the article as failed and continue if:

- article file is missing;
- article file cannot be read;
- article file is empty;
- rendered prompt cannot be created;
- API request fails after retries;
- response has no usable text;
- response JSON is invalid;
- response schema is invalid;
- per-article output cannot be written.

---

## 24. Recommended helper functions

The implementation should be modular.

Recommended functions:

| Function                         | Responsibility                                |
|----------------------------------|-----------------------------------------------|
| `parse_args()`                   | Parse CLI arguments                           |
| `make_config()`                  | Resolve paths and create configuration object |
| `utc_now_iso()`                  | Return UTC timestamp                          |
| `resolve_path()`                 | Resolve relative/absolute paths               |
| `relpath()`                      | Convert paths to stable display paths         |
| `setup_logging()`                | Configure file and console logging            |
| `load_dotenv_file()`             | Load safe environment values                  |
| `validate_basic_options()`       | Validate numeric and required options         |
| `load_prompt()`                  | Read prompt template                          |
| `validate_prompt()`              | Confirm placeholder exists                    |
| `sha256_text()`                  | Hash text                                     |
| `sha256_file()`                  | Hash file                                     |
| `load_manifest_rows()`           | Read NDJSON manifest                          |
| `validate_manifest_row()`        | Validate one manifest row                     |
| `expected_article_output_path()` | Compute per-article JSON path                 |
| `existing_success()`             | Check whether article should be skipped       |
| `read_article_text()`            | Read article file safely                      |
| `build_screening_prompt()`       | Replace article placeholder                   |
| `make_openai_client()`           | Initialise OpenAI client                      |
| `call_openai_with_retries()`     | Call API with retry/backoff                   |
| `extract_response_text()`        | Extract model output text                     |
| `parse_llm_json_response()`      | Parse JSON response                           |
| `validate_screening_response()`  | Validate response schema                      |
| `build_success_record()`         | Build per-article success JSON                |
| `build_failure_record()`         | Build per-article failure JSON                |
| `write_json_file()`              | Write JSON atomically where possible          |
| `write_ndjson_file()`            | Write NDJSON outputs                          |
| `build_run_manifest()`           | Build run-level manifest                      |
| `build_summary()`                | Build compact summary                         |
| `main()`                         | Coordinate full programme                     |

---

## 25. Atomic writes

Where feasible, JSON output files should be written atomically:

```
1. write to temporary file in same directory;
2. flush and close;
3. rename temporary file to final path.
```


This helps prevent corrupted per-article JSON files if the programme is interrupted during a write.

---

## 26. Future extensions

The first version should focus on full-article screening. Future versions may add:

| Feature                                 | Purpose                                        |
|-----------------------------------------|------------------------------------------------|
| `--article-context full                 | seed-windows`                                  | Choose whether to send full article or only evidence windows |
| `--seed-term gaza`                      | Configure term used for context extraction     |
| `--window-paragraphs N`                 | Include N paragraphs around seed-term mentions |
| `--max-input-chars N`                   | Hard cap input size                            |
| `--second-pass-model MODEL`             | Use Terra or Sol for low-confidence cases      |
| `--confidence-threshold FLOAT`          | Trigger second-pass review                     |
| `--category-filter`                     | Reprocess only selected categories             |
| `--failed-only`                         | Reprocess only failed/invalid records          |
| `--batch-api`                           | Use provider batch API                         |
| `--export-core-corpus`                  | Copy or list CORE articles only                |
| `--include-failures-in-screened-ndjson` | Include failed records in consolidated output  |

These are non-goals for the first implementation unless explicitly requested.

---

## 27. Non-goals for first version

The first version should not:

- perform discourse analysis;
- rewrite article text files;
- copy selected articles into a new corpus directory;
- delete excluded articles;
- modify the input manifest;
- infer missing article IDs from filenames unless explicitly configured;
- perform multi-model adjudication;
- use a second-pass model;
- perform automatic sampling;
- build a human annotation interface;
- make judgement about factual correctness or political neutrality;
- classify ideology, sentiment, or framing beyond the prompt’s screening fields.

---

## 28. Acceptance criteria

The programme is acceptable when:

1. It is named `llm_screening.py`.
2. It accepts `--manifest`, `--output`, `--prompt`, and `--model`.
3. It reads an NDJSON manifest containing article metadata and file paths.
4. It treats the input manifest as immutable.
5. It reads prompt instructions from an external Markdown file.
6. It requires the prompt placeholder `<<<ARTICLE_TEXT>>>`.
7. It reads article text from each manifest row’s `filepath`.
8. It supports relative and absolute paths.
9. It reads article files as UTF-8 with replacement for invalid bytes.
10. It calls the OpenAI API unless `--dry-run` is enabled.
11. It uses stateless API calls per article.
12. It parses the LLM response as JSON.
13. It validates the expected screening schema.
14. It writes one per-article JSON artefact per processed article.
15. It preserves the original manifest row in per-article outputs.
16. It records screening results under a structured `screening` object.
17. It records model, prompt hash, article hash, timestamps, duration, and API metadata.
18. It records raw response text for audit/debugging.
19. It writes invalid responses to `llm_screening_invalid_responses.ndjson`.
20. It writes failures to `llm_screening_failures.ndjson`.
21. It writes a consolidated `palestine_now_screened.ndjson`.
22. The consolidated screened NDJSON preserves original manifest order.
23. It writes `llm_screening_manifest.json`.
24. It writes a timestamped/ID-specific manifest.
25. It writes `llm_screening_summary.json`.
26. It writes `llm_screening.log`.
27. It supports `--limit`.
28. It supports `--dry-run`.
29. It supports `--resume`.
30. It supports `--reprocess`.
31. It supports `--workers`.
32. Resume is based on existing successful per-article JSON files.
33. Concurrent workers do not corrupt shared outputs.
34. Per-article failures do not stop the full run.
35. Fatal setup failures occur before API calls.
36. API retries and backoff are implemented.
37. API key values are never logged or written.
38. Prompt and manifest hashes are recorded.
39. Output directory is created if missing.
40. Exit code is `0` when all planned articles succeeded or were skipped.
41. Exit code is non-zero when fatal errors, failed articles, or invalid responses occur.
42. The workflow is suitable for large-scale screening of the full NOW candidate corpus.