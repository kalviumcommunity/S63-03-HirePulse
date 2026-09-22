
import json
from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/raw/missing_data.csv")
OUTPUT_FILE = Path("data/processed/cleaned_data.csv")
DECISION_FILE = Path("output/imputation_decisions.json")


def analyze_missing_values(df):
    """Analyze null counts and percentages before treatment."""

    missing_analysis = pd.DataFrame({
        "column": df.columns,
        "null_count": df.isnull().sum().values,
        "null_percentage": (
            df.isnull().sum() / len(df) * 100
        ).round(2).values,
        "data_type": df.dtypes.astype(str).values,
    })

    print("=" * 70)
    print("BEFORE IMPUTATION - Missing Value Analysis")
    print("=" * 70)
    print(missing_analysis.to_string(index=False))
    print(f"\nTotal rows: {len(df)}")
    print(f"Total cells: {len(df) * len(df.columns)}")
    print(f"Missing cells: {df.isnull().sum().sum()}")
    print("=" * 70)

    return missing_analysis


def drop_rows_with_nulls(df, critical_cols):
    """Drop rows where critical columns are null."""

    rows_before = len(df)
    df_cleaned = df.dropna(subset=critical_cols).copy()
    rows_dropped = rows_before - len(df_cleaned)

    print(
        f"  Dropped {rows_dropped} rows with null in: "
        f"{critical_cols}"
    )

    return df_cleaned


def impute_mode(df, categorical_cols):
    """Fill categorical nulls with the most common value."""

    df_imputed = df.copy()

    for col in categorical_cols:
        null_count = df_imputed[col].isnull().sum()

        if null_count > 0:
            mode_value = df_imputed[col].mode()[0]

            df_imputed[col] = df_imputed[col].fillna(mode_value)

            print(
                f"  {col}: filled {null_count} nulls "
                f"with mode '{mode_value}'"
            )

    return df_imputed


def impute_forward_fill(df, time_series_cols):
    """Forward-fill missing values in time-ordered columns."""

    df_imputed = df.copy()

    for col in time_series_cols:
        null_count = df_imputed[col].isnull().sum()

        if null_count > 0:
            df_imputed[col] = df_imputed[col].ffill()

            print(
                f"  {col}: forward-filled {null_count} nulls"
            )

    return df_imputed


def document_imputation_decisions(df_original, df_imputed):
    """Create an auditable decision log with before/after metrics."""

    nulls_before = int(
        df_original.isnull().sum().sum()
    )

    nulls_after = int(
        df_imputed.isnull().sum().sum()
    )

    decisions = {
        "summary": {
            "rows_before": len(df_original),
            "rows_after": len(df_imputed),
            "rows_removed": (
                len(df_original) - len(df_imputed)
            ),
            "nulls_before": nulls_before,
            "nulls_after": nulls_after,
            "null_reduction": nulls_before - nulls_after,
        },

        "candidate_id": {
            "column_type": "critical_identifier",
            "null_count_before": int(
                df_original["candidate_id"].isnull().sum()
            ),
            "strategy": "drop_rows",
            "business_reasoning": (
                "candidate_id is the primary identifier used to "
                "trace candidate records. Missing identifiers "
                "cannot be safely inferred or fabricated."
            ),
            "risk_assessment": (
                "Low - incomplete records are removed rather "
                "than assigning an incorrect identifier."
            ),
        },

        "email": {
            "column_type": "contact_identifier",
            "null_count_before": int(
                df_original["email"].isnull().sum()
            ),
            "strategy": "drop_rows",
            "business_reasoning": (
                "Email is used as a candidate contact field. "
                "A missing email cannot be safely invented, "
                "so affected records are excluded from the "
                "contactable dataset."
            ),
            "risk_assessment": (
                "Low - only records with missing email are "
                "removed."
            ),
        },

        "department": {
            "column_type": "categorical",
            "null_count_before": int(
                df_original["department"].isnull().sum()
            ),
            "strategy": "mode_imputation",
            "value_used": str(
                df_original["department"].mode()[0]
            ),
            "business_reasoning": (
                "Department is categorical. The most common "
                "department provides a simple representative "
                "value without creating a new category."
            ),
            "risk_assessment": (
                "Medium - the missing candidate may belong to "
                "a different department."
            ),
        },

        "applied_date": {
            "column_type": "time_series",
            "null_count_before": int(
                df_original["applied_date"].isnull().sum()
            ),
            "strategy": "forward_fill",
            "business_reasoning": (
                "The records are ordered by application date. "
                "Forward fill preserves temporal continuity "
                "when a date is missing between known observations."
            ),
            "risk_assessment": (
                "Medium - assumes the previous known date is "
                "an acceptable value for the missing observation."
            ),
        },

        "phone": {
            "column_type": "contact_information",
            "null_count_before": int(
                df_original["phone"].isnull().sum()
            ),
            "strategy": "leave_null",
            "business_reasoning": (
                "A missing phone number should not be fabricated. "
                "There is insufficient information to infer the "
                "candidate's real phone number."
            ),
            "risk_assessment": (
                "Low - the missing value remains visible and "
                "documented instead of introducing false data."
            ),
        },
    }

    DECISION_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        DECISION_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            decisions,
            file,
            indent=2,
        )

    return decisions


def validate_imputation(df_original, df_imputed):
    """Compare before and after metrics."""

    total_nulls_before = int(
        df_original.isnull().sum().sum()
    )

    total_nulls_after = int(
        df_imputed.isnull().sum().sum()
    )

    print("\n" + "=" * 70)
    print("AFTER IMPUTATION - Validation Report")
    print("=" * 70)

    print(f"Total rows before: {len(df_original)}")
    print(f"Total rows after:  {len(df_imputed)}")

    print(
        f"Rows removed:     "
        f"{len(df_original) - len(df_imputed)}"
    )

    print(
        f"\nTotal nulls before: {total_nulls_before}"
    )

    print(
        f"Total nulls after:  {total_nulls_after}"
    )

    missing_after = pd.DataFrame({
        "column": df_imputed.columns,
        "null_count_after": df_imputed.isnull().sum().values,
        "null_percentage_after": (
            df_imputed.isnull().sum()
            / len(df_imputed)
            * 100
        ).round(2).values,
    })

    print("\nNull values by column after treatment:")
    print(missing_after.to_string(index=False))

    print("=" * 70)

    return missing_after


def main():
    """Run the complete missing-value handling workflow."""

    print(
        "Loading HirePulse missing-value test dataset..."
    )

    df_original = pd.read_csv(
        INPUT_FILE,
        skipinitialspace=True,
    )

    # Treat blank strings as missing values.
    df_original = df_original.replace(
        r"^\s*$",
        pd.NA,
        regex=True,
    )

    # Convert applied_date to datetime for time-series handling.
    df_original["applied_date"] = pd.to_datetime(
        df_original["applied_date"],
        errors="coerce",
    )

    print("\nStep 1: Analyzing missing values...")
    analyze_missing_values(df_original)

    print(
        "\nStep 2: Applying imputation strategies..."
    )

    # Critical fields: remove incomplete records.
    df_cleaned = drop_rows_with_nulls(
        df_original,
        ["candidate_id", "email"],
    )

    # Categorical field: mode.
    df_cleaned = impute_mode(
        df_cleaned,
        ["department"],
    )

    # Time-series field: forward fill.
    df_cleaned = impute_forward_fill(
        df_cleaned,
        ["applied_date"],
    )

    print(
        "\nStep 3: Documenting decisions..."
    )

    document_imputation_decisions(
        df_original,
        df_cleaned,
    )

    print(
        "\nStep 4: Validating treatment..."
    )

    validate_imputation(
        df_original,
        df_cleaned,
    )

    # Save cleaned data.
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df_cleaned.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nCleaned data saved to: {OUTPUT_FILE}"
    )

    print(
        f"Decision log saved to: {DECISION_FILE}"
    )


if __name__ == "__main__":
    main()

