"""Standalone Date & Time Transformation Pipeline for Assignment 2.22."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "transactions.csv"
TRANSFORMED_PATH = PROJECT_ROOT / "data" / "processed" / "transformed_transactions.csv"
FEATURE_REPORT_PATH = PROJECT_ROOT / "output" / "datetime_feature_report.csv"
WEEKLY_SUMMARY_PATH = PROJECT_ROOT / "output" / "weekly_revenue_summary.csv"


def validate_outputs(
    transformed: pd.DataFrame, weekly_revenue: pd.Series
) -> None:
    """Validate the required datetime features and weekly aggregation."""
    required_features = {
        "day_of_week",
        "hour",
        "week_num",
        "month",
        "quarter",
        "days_since_transaction",
    }

    assert transformed["transaction_date"].dtype == "datetime64[ns]"
    assert required_features.issubset(transformed.columns)
    assert isinstance(weekly_revenue, pd.Series)
    assert not weekly_revenue.empty


def main() -> None:
    """Run the standalone datetime transformation pipeline."""
    TRANSFORMED_PATH.parent.mkdir(parents=True, exist_ok=True)
    FEATURE_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_PATH)
    original_dtypes = df.dtypes.rename("original_dtype").astype(str)

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        format="%Y-%m-%d %H:%M:%S",
    )
    today = pd.Timestamp.now()
    df["day_of_week"] = df["transaction_date"].dt.day_name()
    df["hour"] = df["transaction_date"].dt.hour
    df["week_num"] = df["transaction_date"].dt.isocalendar().week
    df["month"] = df["transaction_date"].dt.month
    df["quarter"] = df["transaction_date"].dt.quarter
    df["days_since_transaction"] = (today - df["transaction_date"]).dt.days

    converted_dtypes = df.dtypes.rename("converted_dtype").astype(str)
    feature_report = pd.DataFrame(
        {
            "feature": [
                "day_of_week",
                "hour",
                "week_num",
                "month",
                "quarter",
                "days_since_transaction",
            ],
            "dtype": [str(df[feature].dtype) for feature in [
                "day_of_week",
                "hour",
                "week_num",
                "month",
                "quarter",
                "days_since_transaction",
            ]],
        }
    )

    weekly_revenue = (
        df.set_index("transaction_date")["amount"]
        .resample("W")
        .sum()
        .rename("weekly_revenue")
    )

    validate_outputs(df, weekly_revenue)
    df.to_csv(TRANSFORMED_PATH, index=False)
    feature_report.to_csv(FEATURE_REPORT_PATH, index=False)
    weekly_revenue.to_frame().to_csv(WEEKLY_SUMMARY_PATH)

    print("Original dtypes")
    print(original_dtypes.to_string())
    print("\nConverted dtypes")
    print(converted_dtypes.to_string())
    print("\nCreated feature columns")
    print(feature_report["feature"].to_list())
    print("\nWeekly aggregation preview")
    print(weekly_revenue.head().to_string())
    print("\nOutput file locations")
    print(TRANSFORMED_PATH)
    print(FEATURE_REPORT_PATH)
    print(WEEKLY_SUMMARY_PATH)
    print("\nDate & Time Transformation Pipeline completed successfully.")


if __name__ == "__main__":
    main()