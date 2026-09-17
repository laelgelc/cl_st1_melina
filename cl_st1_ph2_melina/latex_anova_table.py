#!/usr/bin/env python3
"""
Generate a LaTeX ANOVA table for group effects.

Each table row lists F, p, R², and percent R² for one factor dimension.

Default expected inputs:
    sas/output_<project>/<project>_scores_only.tsv
    sas/output_<project>/anova_group_f<n>.tsv
    sas/output_<project>/params_group_f<n>.tsv

Default output:
    latex_tables/anova_group.tex

The project name is inferred from the current working directory unless supplied
explicitly with --project.

The script handles SAS-style p-values such as:
    <.0001

Typical usage from the project root:
    python latex_anova_table.py

Optional explicit usage:
    python latex_anova_table.py \
        --project cl_st1_ph2_melina \
        --input-dir sas/output_cl_st1_ph2_melina \
        --output-dir latex_tables
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import pandas as pd


DEFAULT_PROJECT = Path.cwd().name
DEFAULT_OUTPUT_DIR = Path("latex_tables")
DEFAULT_EFFECT = "group"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate LaTeX ANOVA table for group effects."
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
        "--input-dir",
        default=None,
        help=(
            "Directory containing SAS ANOVA outputs. "
            "Default: sas/output_<project>."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where LaTeX table files will be written.",
    )
    parser.add_argument(
        "--effect",
        default=DEFAULT_EFFECT,
        help=(
            "Model effect/source name to report. "
            "Default: group."
        ),
    )

    return parser.parse_args()


def resolve_input_dir(project: str, input_dir_arg: str | None) -> Path:
    """Resolve the SAS output directory."""
    if input_dir_arg is None:
        return Path("sas") / f"output_{project}"

    return Path(input_dir_arg)


def read_rsquare(path: Path) -> float:
    """Read RSquare from the first row of a TSV file."""
    if not path.exists():
        raise FileNotFoundError(f"R-square parameter file not found: {path}")

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)

    if not rows:
        return 0.0

    if "RSquare" not in rows[0]:
        raise ValueError(f"Column 'RSquare' not found in {path}")

    return float(rows[0]["RSquare"])


def format_rsquare(rsquare: float) -> tuple[str, str]:
    """Return R² without leading zero, plus percent R²."""
    actual = f"{rsquare:.5f}"

    if actual.startswith("0"):
        actual = actual[1:]

    return actual, f"{rsquare * 100:.2f}"


def parse_sas_p_value(value) -> tuple[float, str | None]:
    """
    Parse p-values exported by SAS.

    SAS may write very small p-values as:
        <.0001

    Returns:
        numeric p-value for logic
        display override if the original value should be preserved
    """
    text = str(value).strip()

    if text.startswith("<"):
        threshold = text[1:].strip()

        if threshold.startswith("."):
            threshold = "0" + threshold

        return float(threshold), text

    return float(text), None


def format_p_value(value: float, display_override: str | None = None) -> str:
    """Format p-values for LaTeX table output."""
    if display_override is not None:
        return display_override.replace("<.", "< .")

    if value < 0.001:
        return "< .001"

    return f"{value:.3f}"


def latex_escape(text: str) -> str:
    """Escape characters that have special meaning in LaTeX."""
    replacements = {
        "\\": r"\textbackslash{}",
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "{": r"\{",
        "}": r"\}",
        "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}",
    }

    for original, escaped in replacements.items():
        text = text.replace(original, escaped)

    return text


def detect_dims(scores_only_path: Path) -> list[int]:
    """Detect available factor dimensions from columns fac1, fac2, etc."""
    if not scores_only_path.exists():
        raise FileNotFoundError(f"Scores-only file not found: {scores_only_path}")

    df = pd.read_csv(scores_only_path, sep="\t", nrows=1)
    factor_columns = [
        column for column in df.columns
        if re.fullmatch(r"fac\d+", str(column))
    ]

    dims = sorted({int(str(column)[3:]) for column in factor_columns})

    if not dims:
        raise RuntimeError(f"No fac<n> columns found in {scores_only_path}")

    return dims


def read_anova_row(anova_file: Path, source_name: str) -> pd.Series:
    """Read the relevant ModelANOVA row for the requested source name."""
    if not anova_file.exists():
        raise FileNotFoundError(f"ANOVA file not found: {anova_file}")

    df = pd.read_csv(anova_file, sep="\t")

    required_columns = {"HypothesisType", "Source", "FValue", "ProbF"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"{anova_file} is missing required columns: "
            f"{', '.join(sorted(missing_columns))}"
        )

    source_name_lc = source_name.lower()

    selected = df[
        (df["HypothesisType"] == 1)
        & (df["Source"].astype(str).str.lower() == source_name_lc)
    ]

    if selected.empty:
        selected = df[df["HypothesisType"] == 1]

    if selected.empty:
        raise ValueError(f"No HypothesisType == 1 row found in {anova_file}")

    return selected.iloc[0]


def make_effect_table(
        input_dir: Path,
        output_dir: Path,
        dims: list[int],
        effect: str,
) -> Path:
    """Create the LaTeX ANOVA table for the requested effect."""
    rows = []

    for dim in dims:
        anova_file = input_dir / f"anova_{effect}_f{dim}.tsv"
        params_file = input_dir / f"params_{effect}_f{dim}.tsv"

        anova_row = read_anova_row(anova_file, source_name=effect)

        f_value = float(anova_row["FValue"])
        p_value, p_display_override = parse_sas_p_value(anova_row["ProbF"])

        rsquare = read_rsquare(params_file)
        r2_actual, r2_percent = format_rsquare(rsquare)

        rows.append(
            (
                dim,
                f"{f_value:.2f}",
                format_p_value(p_value, p_display_override),
                r2_actual,
                r2_percent,
            )
        )

    output_dir.mkdir(exist_ok=True, parents=True)
    output_path = output_dir / f"anova_{effect}.tex"

    effect_title = effect.replace("_", " ").title()
    escaped_effect = latex_escape(effect)

    with output_path.open("w", encoding="utf-8") as f:
        f.write("\\begin{table}[H]\n")
        f.write("  \\centering\n")
        f.write(f"  \\caption{{ANOVA Results by {effect_title}}}\n")
        f.write(f"  \\label{{tab:anova_{escaped_effect}}}\n")
        f.write("  \\begin{tabular}{l r r r r}\n")
        f.write("    Dim. & F & p & R$^2$ & \\% \\\\\n")
        f.write("    \\hline\n")

        for dim, f_value, p_value, r2_actual, r2_percent in rows:
            f.write(
                f"    {dim} & {f_value} & {p_value} & "
                f"{r2_actual} & {r2_percent} \\\\\n"
            )

        f.write("  \\end{tabular}\n")
        f.write("\\end{table}\n")

    return output_path


def main() -> None:
    """Run LaTeX ANOVA table generation."""
    args = parse_args()

    project = args.project
    effect = args.effect.strip()
    input_dir = resolve_input_dir(project, args.input_dir)
    output_dir = Path(args.output_dir)

    if not effect:
        raise ValueError("--effect must not be empty")

    scores_only_path = input_dir / f"{project}_scores_only.tsv"
    dims = detect_dims(scores_only_path)

    output_path = make_effect_table(
        input_dir=input_dir,
        output_dir=output_dir,
        dims=dims,
        effect=effect,
    )

    print(f"Project: {project}")
    print(f"Effect: {effect}")
    print(f"Input directory: {input_dir}")
    print(f"Detected dimensions: {', '.join(map(str, dims))}")
    print(f"LaTeX ANOVA table written to: {output_path}")


if __name__ == "__main__":
    main()