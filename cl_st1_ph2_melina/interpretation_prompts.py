#!/usr/bin/env python3
"""
Generate interpretation prompt files for factor poles.

For each pole, this script assembles a complete prompt containing:
    1. System prompt
    2. User prompt
    3. Mean group scores
    4. Factor loadings
    5. Example excerpts, with their loading words appended

The project name is inferred from the current working directory unless supplied
explicitly with --project.

Expected inputs:
    factors/f<n>_<pole>.txt
    examples_txt/f<n>_<pole>/*.txt
    examples/score_details.txt
    sas/output_<project>/means_group_f<n>.tsv

Compatibility fallback:
    sas/output_<project>/means_decade_f<n>.tsv

Output:
    interpretation/input/f<n>_<pole>.txt
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


# ============================================================
# DEFAULTS
# ============================================================

DEFAULT_PROJECT = Path.cwd().name
DEFAULT_FACTORS_DIR = Path("factors")
DEFAULT_EXAMPLES_DIR = Path("examples_txt")
DEFAULT_DETAILS_FILE = Path("examples/score_details.txt")
DEFAULT_OUTPUT_DIR = Path("interpretation/input")
DEFAULT_EXCERPT_COUNT = 10
DEFAULT_EXCERPT_LINES = 30


# ============================================================
# ARGUMENTS
# ============================================================

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate LLM interpretation prompts for factor poles."
    )

    parser.add_argument(
        "--project",
        default=DEFAULT_PROJECT,
        help=(
            "Project name, e.g. cl_st1_ph2_melina or cl_st1_ph3_melina. "
            "Default: current directory name."
        ),
    )
    parser.add_argument(
        "--sas-output-dir",
        default=None,
        help=(
            "Directory containing SAS outputs. "
            "Default: sas/output_<project>."
        ),
    )
    parser.add_argument(
        "--factors-dir",
        default=str(DEFAULT_FACTORS_DIR),
        help="Directory containing factor loading files. Default: factors.",
    )
    parser.add_argument(
        "--examples-dir",
        default=str(DEFAULT_EXAMPLES_DIR),
        help="Directory containing plaintext example files. Default: examples_txt.",
    )
    parser.add_argument(
        "--details-file",
        default=str(DEFAULT_DETAILS_FILE),
        help="Path to score_details.txt. Default: examples/score_details.txt.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory for interpretation prompts. Default: interpretation/input.",
    )
    parser.add_argument(
        "--excerpt-count",
        type=int,
        default=DEFAULT_EXCERPT_COUNT,
        help="Maximum number of examples to include per pole.",
    )
    parser.add_argument(
        "--excerpt-lines",
        type=int,
        default=DEFAULT_EXCERPT_LINES,
        help="Maximum number of lines to include from each example file.",
    )

    return parser.parse_args()


def resolve_sas_output_dir(project: str, sas_output_dir_arg: str | None) -> Path:
    """Resolve the SAS output directory."""
    if sas_output_dir_arg is None:
        return Path("sas") / f"output_{project}"

    return Path(sas_output_dir_arg)


def resolve_means_file(sas_output_dir: Path, factor_number: str) -> Path:
    """Resolve group-means file, with compatibility fallback for older names."""
    candidates = [
        sas_output_dir / f"means_group_f{factor_number}.tsv",
        sas_output_dir / f"means_decade_f{factor_number}.tsv",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Required means file missing. Expected one of:\n"
        + "\n".join(f"  - {candidate}" for candidate in candidates)
    )


# ============================================================
# PROMPT TEXT
# ============================================================

def phase_description(project: str) -> str:
    """Return a phase-specific description for the current project."""
    project_lower = project.lower()

    if "ph2" in project_lower:
        return (
            "This phase analyses the IQR-capped robustness corpus of NOW news articles "
            "on Palestine/Gaza-related discourse. The corpus is grouped by Global North/South "
            "classification and publication month, with a cap applied to reduce the dominance "
            "of highly represented groups."
        )

    if "ph3" in project_lower:
        return (
            "This phase analyses the IQR-filtered corpus of NOW news articles "
            "on Palestine/Gaza-related discourse. The corpus is grouped by Global North/South "
            "classification and publication month, retaining articles within the interquartile "
            "range of article length."
        )

    return (
        "This phase analyses a corpus of NOW news articles on Palestine/Gaza-related discourse, "
        "grouped by Global North/South classification and publication month."
    )


def build_system_prompt(project: str) -> str:
    """Build the system prompt."""
    return f"""You are a corpus linguist specialising in Lexical Multi-Dimensional Analysis (LMDA).
Your task is to interpret a single factor pole as a discourse dimension.

The corpus consists of selected NOW news articles on Palestine/Gaza-related discourse.
The texts are organised by group, where each group combines:
• Global North or Global South classification;
• publication year;
• publication month.

Example group labels have the form:
• global_north_2023_09
• global_south_2023_09

{phase_description(project)}

The analysis is applied to group-based strata rather than decade-based strata.
The corpus should not be assumed to be fully balanced unless the supplied mean scores
or project documentation explicitly show that it is. Treat group differences as
potentially meaningful evidence of temporal, geopolitical, or sampling-related patterns.

Your interpretation must identify the discourses encoded at this pole, taking into account:
• lexical loadings, which represent the full analysed corpus;
• example excerpts, which illustrate high-scoring texts at this pole;
• the groups that score most strongly at this pole.
"""


USER_PROMPT = """Interpret Factor {factor} ({polarity}) as a discourse dimension.
Propose possible labels for this pole only and justify them.

Base your interpretation on:
• Mean group scores. For positive poles, consider the highest-scoring groups in the table. For negative poles, consider the lowest-scoring groups; these may be the lowest positive scores or the most negative scores if there are any.
• Factor loadings.
• Example excerpts from high-scoring texts.
• The loading words that appear in these examples.
• Which groups appear to drive this pole.
• Any Global North/South, month-by-month, or diachronic tendencies suggested by the group scores.

Do not offer a "versus" interpretation of the opposite pole.
Focus on this single pole only.

Give equal weight to the loadings and the examples. Remember that loadings represent the full analysed corpus, whereas the excerpts are only a limited set of high-scoring samples.
Do not assume that the corpus is fully balanced across groups. If group scores appear uneven, discuss them cautiously as potentially reflecting discourse, historical salience, or sampling structure.
"""


# ============================================================
# LOAD SCORE DETAILS
# ============================================================

def load_score_details(details_path: Path) -> dict[str, dict[str, dict[str, list[str]]]]:
    """
    Parse score_details.txt into:
        score_details[text_id][factor]["pos" or "neg"] = list_of_words
    """
    if not details_path.exists():
        raise FileNotFoundError(f"Score details file not found: {details_path}")

    score_details: dict[str, dict[str, dict[str, list[str]]]] = {}
    current_id = None
    current_factor = None

    with details_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            match_id = re.match(r"text ID:\s*(t\d+)", line)
            if match_id:
                current_id = match_id.group(1)
                score_details[current_id] = {}
                current_factor = None
                continue

            match_factor = re.match(r"(f\d+)\s+score:", line)
            if match_factor and current_id:
                current_factor = match_factor.group(1)
                score_details[current_id][current_factor] = {
                    "pos": [],
                    "neg": [],
                }
                continue

            match_words = re.match(r"f\d+\s+(pos|neg)\s+words.*:\s*(.*)", line)
            if match_words and current_id and current_factor:
                pole = match_words.group(1)
                words_string = match_words.group(2).strip()
                words = [
                    word.strip()
                    for word in words_string.split(",")
                    if word.strip()
                ]
                score_details[current_id][current_factor][pole] = words

    return score_details


# ============================================================
# EXCERPT EXTRACTOR
# ============================================================

def extract_excerpt(file_path: Path, n_lines: int) -> str:
    """Extract the first n_lines from an example text file."""
    lines = []

    with file_path.open("r", encoding="utf-8") as f:
        for _ in range(n_lines):
            line = f.readline()

            if not line:
                break

            lines.append(line.rstrip("\n"))

    return "\n".join(lines)


def detect_text_id(text: str) -> str | None:
    """Detect a text ID such as t000001 inside an example file."""
    match = re.search(r"(t\d{6})", text)

    if match:
        return match.group(1)

    return None


def natural_sort_key(path: Path) -> list[int | str]:
    """Return a natural-sort key for paths."""
    parts = re.split(r"(\d+)", path.name)
    return [int(part) if part.isdigit() else part.lower() for part in parts]


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """Build all interpretation prompt files."""
    args = parse_args()

    project = args.project
    sas_output_dir = resolve_sas_output_dir(project, args.sas_output_dir)
    factors_dir = Path(args.factors_dir)
    examples_dir = Path(args.examples_dir)
    details_file = Path(args.details_file)
    output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    if not factors_dir.exists():
        raise FileNotFoundError(f"Factors directory not found: {factors_dir}")

    if not examples_dir.exists():
        raise FileNotFoundError(f"Examples directory not found: {examples_dir}")

    if not sas_output_dir.exists():
        raise FileNotFoundError(f"SAS output directory not found: {sas_output_dir}")

    score_details = load_score_details(details_file)

    factor_files = sorted(
        factors_dir.glob("f*_*.txt"),
        key=natural_sort_key,
    )

    if not factor_files:
        raise FileNotFoundError(f"No factor pole files found in {factors_dir}")

    system_prompt = build_system_prompt(project)

    for factor_file in factor_files:
        factor_name = factor_file.stem

        parts = factor_name.split("_")
        if len(parts) != 2:
            print(f"Warning: skipping unexpected factor filename: {factor_file}")
            continue

        factor = parts[0]
        polarity = parts[1]

        if polarity not in {"pos", "neg"}:
            print(f"Warning: skipping unexpected polarity in: {factor_file}")
            continue

        factor_number = factor.replace("f", "")

        loadings_text = factor_file.read_text(encoding="utf-8").strip()

        try:
            means_file = resolve_means_file(sas_output_dir, factor_number)
        except FileNotFoundError as error:
            print(f"Warning: {error}")
            means_text = "(No means file found)"
        else:
            means_text = means_file.read_text(encoding="utf-8").strip()

        example_folder = examples_dir / factor_name

        if not example_folder.exists():
            print(f"Warning: missing example folder {example_folder}")
            example_files = []
        else:
            example_files = sorted(
                example_folder.glob("*.txt"),
                key=natural_sort_key,
            )[:args.excerpt_count]

        excerpts_block = []

        for example_path in example_files:
            excerpt = extract_excerpt(example_path, args.excerpt_lines)
            file_text = example_path.read_text(encoding="utf-8")

            text_id = detect_text_id(file_text)

            if not text_id:
                print(f"Warning: no text ID found in {example_path}")
                continue

            loading_words = (
                score_details
                .get(text_id, {})
                .get(factor, {})
                .get(polarity, [])
            )

            loading_words_string = (
                ", ".join(loading_words)
                if loading_words
                else "(none)"
            )

            excerpt_block = (
                f"\n===== EXCERPT: {example_path.name} "
                f"(text ID {text_id}) =====\n"
                f"{excerpt}\n"
                f"\n--- Loading words for this example ({polarity}): "
                f"{loading_words_string}\n"
            )

            excerpts_block.append(excerpt_block)

        user_prompt = USER_PROMPT.format(
            factor=factor,
            polarity=polarity,
        )

        mean_section = f"\n=== MEAN GROUP SCORES ===\n{means_text}\n"
        loadings_section = f"\n=== FACTOR LOADINGS ({factor_name}) ===\n{loadings_text}\n"

        final_prompt = (
            system_prompt
            + "\n\n"
            + user_prompt
            + "\n"
            + mean_section
            + loadings_section
            + "\n=== EXAMPLE EXCERPTS ===\n"
            + "\n".join(excerpts_block)
        )

        output_path = output_dir / f"{factor_name}.txt"
        output_path.write_text(final_prompt, encoding="utf-8")

        print("Wrote:", output_path)

    print(f"\nProject: {project}")
    print(f"SAS output directory: {sas_output_dir}")
    print(f"Interpretation prompts written to: {output_dir}")


if __name__ == "__main__":
    main()