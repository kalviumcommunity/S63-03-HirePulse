"""Standalone outlier detection pipeline for Assignment 2.23."""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "customer_revenue.csv"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" / "revenue_outlier_processed.csv"
CLEANING_LOG_PATH = PROJECT_ROOT / "output" / "cleaning_log.csv"
SUMMARY_PATH = PROJECT_ROOT / "output" / "outlier_summary.csv"
RECORDS_PATH = PROJECT_ROOT / "output" / "outlier_records.csv"


def validate_outputs(
    df: pd.DataFrame,
    cleaning_log: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    """Validate required columns and generated output reports."""
    required_columns = {
        "revenue_zscore",
        "revenue_z_outlier",
        "is_outlier_iqr",
        "revenue_capped",
        "is_outlier",
        "age_outlier",
    }
    assert required_columns.issubset(df.columns)
    assert CLEANING_LOG_PATH.exists()
    assert SUMMARY_PATH.exists()
    assert RECORDS_PATH.exists()
    assert PROCESSED_PATH.exists()
    assert set(cleaning_log.columns) == {
        "column",
        "method",
        "action",
        "threshold_lower",
        "threshold_upper",
        "affected_rows",
        "reason",
        "timestamp",
    }
    assert list(summary.columns) == ["Metric", "Value"]


def main() -> None:
    """Run the standalone outlier detection and cleaning pipeline."""
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLEANING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_PATH)
    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    print(f"Dataset shape: {df.shape}")
    print(f"Column names: {df.columns.tolist()}")
    print(f"Numeric columns: {numeric_columns}")

    df["revenue_zscore"] = np.abs(stats.zscore(df["revenue"]))
    df["revenue_z_outlier"] = df["revenue_zscore"] > 3

    q1 = df["revenue"].quantile(0.25)
    q3 = df["revenue"].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    df["is_outlier_iqr"] = (
        (df["revenue"] < lower_bound) | (df["revenue"] > upper_bound)
    )

    original_min = df["revenue"].min()
    original_max = df["revenue"].max()
    df["revenue_capped"] = df["revenue"].clip(
        lower=lower_bound,
        upper=upper_bound,
    )
    capped_rows = int((df["revenue"] != df["revenue_capped"]).sum())
    capped_min = df["revenue_capped"].min()
    capped_max = df["revenue_capped"].max()

    df["is_outlier"] = (
        df["is_outlier_iqr"] | df["revenue_z_outlier"]
    ).astype(int)
    df["age_outlier"] = df["age"] > 120

    zscore_count = int(df["revenue_z_outlier"].sum())
    iqr_count = int(df["is_outlier_iqr"].sum())
    age_count = int(df["age_outlier"].sum())
    flagged_rows = int(df["is_outlier"].sum())
    timestamp = pd.Timestamp.now().isoformat()
    cleaning_log = pd.DataFrame(
        [
            {
                "column": "revenue",
                "method": "IQR",
                "action": "Cap",
                "threshold_lower": lower_bound,
                "threshold_upper": upper_bound,
                "affected_rows": capped_rows,
                "reason": "Cap revenue values outside IQR bounds",
                "timestamp": timestamp,
            },
            {
                "column": "age",
                "method": "Business Rule",
                "action": "Flag",
                "threshold_lower": None,
                "threshold_upper": 120,
                "affected_rows": age_count,
                "reason": "Flag impossible ages greater than 120",
                "timestamp": timestamp,
            },
            {
                "column": "revenue",
                "method": "Z-Score + IQR",
                "action": "Flag",
                "threshold_lower": lower_bound,
                "threshold_upper": upper_bound,
                "affected_rows": flagged_rows,
                "reason": "Combine statistical outlier detection methods",
                "timestamp": timestamp,
            },
        ]
    )

    summary = pd.DataFrame(
        {
            "Metric": [
                "Total Records",
                "Revenue Outliers",
                "Age Outliers",
                "Rows Capped",
                "Rows Flagged",
            ],
            "Value": [len(df), iqr_count, age_count, capped_rows, flagged_rows],
        }
    )
    outlier_records = df[(df["is_outlier"] == 1) | df["age_outlier"]]

    df.to_csv(PROCESSED_PATH, index=False)
    cleaning_log.to_csv(CLEANING_LOG_PATH, index=False)
    summary.to_csv(SUMMARY_PATH, index=False)
    outlier_records.to_csv(RECORDS_PATH, index=False)
    validate_outputs(df, cleaning_log, summary)

    print(f"Z-score outliers count: {zscore_count}")
    print(f"IQR outliers count: {iqr_count}")
    print(f"Age outliers count: {age_count}")
    print(f"Q1: {q1}")
    print(f"Q3: {q3}")
    print(f"IQR: {iqr}")
    print(f"Lower Bound: {lower_bound}")
    print(f"Upper Bound: {upper_bound}")
    print(f"Original Min: {original_min}")
    print(f"Original Max: {original_max}")
    print(f"Capped Min: {capped_min}")
    print(f"Capped Max: {capped_max}")
    print(f"Rows capped: {capped_rows}")
    print(f"Rows flagged: {flagged_rows}")
    print("Output file locations:")
    print(PROCESSED_PATH)
    print(CLEANING_LOG_PATH)
    print(SUMMARY_PATH)
    print(RECORDS_PATH)
    print("Outlier Detection Pipeline completed successfully.")


if __name__ == "__main__":
    main()