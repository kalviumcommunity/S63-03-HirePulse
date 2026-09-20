"""Standalone Assignment 2.19 type-enforcement workflow."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "untyped_data.csv"
TYPED_OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "typed_data.csv"
REPORT_OUTPUT_FILE = PROJECT_ROOT / "output" / "dtype_conversion_report.csv"


def cast_columns_to_types(
    frame: pd.DataFrame,
    column_types: dict[str, str],
) -> pd.DataFrame:
    """Cast columns with pandas dtype names and return a copy."""
    converted = frame.copy()
    for column, dtype in column_types.items():
        converted[column] = converted[column].astype(dtype)
    return converted


def convert_string_dates_to_datetime(
    frame: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """Convert string date columns to pandas datetime values."""
    converted = frame.copy()
    for column in columns:
        converted[column] = pd.to_datetime(converted[column], errors="coerce")
    return converted


def convert_currency_to_float(
    frame: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """Remove currency formatting and convert amounts to float."""
    converted = frame.copy()
    for column in columns:
        values = converted[column].astype("string").str.replace(
            r"[^0-9.-]", "", regex=True
        )
        converted[column] = pd.to_numeric(values, errors="coerce").astype(float)
    return converted


def convert_integers_to_boolean(
    frame: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """Convert integer flags, using zero as false and nonzero as true."""
    converted = frame.copy()
    for column in columns:
        converted[column] = converted[column].astype(bool)
    return converted


def compare_dtypes(before: pd.DataFrame, after: pd.DataFrame) -> pd.DataFrame:
    """Return a column-by-column before/after dtype comparison."""
    comparison = pd.DataFrame(
        {
            "column": before.columns,
            "before_dtype": [str(before[column].dtype) for column in before.columns],
            "after_dtype": [str(after[column].dtype) for column in before.columns],
        }
    )
    comparison["changed"] = comparison["before_dtype"] != comparison["after_dtype"]
    return comparison


def main() -> None:
    """Run the complete standalone type-conversion workflow."""
    source = pd.read_csv(INPUT_FILE)
    print("Before dtypes:")
    print(source.dtypes.to_string())

    typed = cast_columns_to_types(source, {"user_id": "int64"})
    typed = convert_string_dates_to_datetime(
        typed,
        ["transaction_date", "signup_date"],
    )
    typed = convert_currency_to_float(typed, ["amount", "revenue"])
    typed = convert_integers_to_boolean(typed, ["is_active", "is_premium"])

    comparison = compare_dtypes(source, typed)
    TYPED_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    typed.to_csv(TYPED_OUTPUT_FILE, index=False, date_format="%Y-%m-%d")
    comparison.to_csv(REPORT_OUTPUT_FILE, index=False)

    print("\nAfter dtypes:")
    print(typed.dtypes.to_string())
    print("\nConversion summary:")
    print(comparison.to_string(index=False))
    print(f"\nTyped data saved to: {TYPED_OUTPUT_FILE}")
    print(f"Dtype report saved to: {REPORT_OUTPUT_FILE}")


if __name__ == "__main__":
    main()