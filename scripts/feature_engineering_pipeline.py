import logging
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "customer_features.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"
ENGINEERED_PATH = OUTPUT_DIR / "customer_features_engineered.csv"
SUMMARY_PATH = OUTPUT_DIR / "feature_summary_report.csv"
VALIDATION_PATH = OUTPUT_DIR / "feature_validation_report.csv"

LOGGER = logging.getLogger(__name__)
ENGINEERED_COLUMNS = [
    "transactions_per_month",
    "avg_spend_per_transaction",
    "lifetime_value_per_month",
    "engagement_tier",
    "spend_quartile",
    "recency_score",
    "frequency_score",
    "monetary_score",
    "rfm_score",
]
NUMERIC_ENGINEERED_COLUMNS = [
    "transactions_per_month",
    "avg_spend_per_transaction",
    "lifetime_value_per_month",
    "recency_score",
    "frequency_score",
    "monetary_score",
    "rfm_score",
]


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def engineer_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.copy()
    dataframe["transactions_per_month"] = dataframe["total_transactions"] / (
        dataframe["days_as_customer"] / 30
    )
    dataframe["avg_spend_per_transaction"] = (
        dataframe["total_spent"] / dataframe["total_transactions"]
    )
    dataframe["lifetime_value_per_month"] = dataframe["total_spent"] / (
        dataframe["days_as_customer"] / 30
    )
    dataframe["engagement_tier"] = pd.cut(
        dataframe["transactions_per_month"],
        bins=[0, 2, 10, float("inf")],
        labels=["low", "medium", "high"],
    )
    dataframe["spend_quartile"] = pd.qcut(
        dataframe["total_spent"], q=4, labels=["Q1", "Q2", "Q3", "Q4"]
    )
    dataframe["recency_score"] = pd.qcut(
        dataframe["days_since_last_purchase"], q=5, labels=[5, 4, 3, 2, 1]
    ).astype(int)
    dataframe["frequency_score"] = pd.qcut(
        dataframe["purchase_count"], q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    dataframe["monetary_score"] = pd.qcut(
        dataframe["total_spent"], q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    dataframe["rfm_score"] = (
        dataframe["recency_score"]
        + dataframe["frequency_score"]
        + dataframe["monetary_score"]
    )
    return dataframe


def create_summary_report(dataframe: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "feature_name": NUMERIC_ENGINEERED_COLUMNS,
            "dtype": [str(dataframe[column].dtype) for column in NUMERIC_ENGINEERED_COLUMNS],
            "min": [dataframe[column].min() for column in NUMERIC_ENGINEERED_COLUMNS],
            "max": [dataframe[column].max() for column in NUMERIC_ENGINEERED_COLUMNS],
            "mean": [dataframe[column].mean() for column in NUMERIC_ENGINEERED_COLUMNS],
        }
    )


def create_validation_report(dataframe: pd.DataFrame) -> pd.DataFrame:
    checks = [
        (
            "no_missing_engineered_features",
            not dataframe[ENGINEERED_COLUMNS].isna().any().any(),
            "No NaNs in engineered feature columns",
        ),
        (
            "rfm_score_range",
            dataframe["rfm_score"].between(3, 15).all(),
            "RFM scores are between 3 and 15",
        ),
        (
            "positive_transactions_per_month",
            (dataframe["transactions_per_month"] > 0).all(),
            "All transactions_per_month values are positive",
        ),
        (
            "positive_avg_spend_per_transaction",
            (dataframe["avg_spend_per_transaction"] > 0).all(),
            "All avg_spend_per_transaction values are positive",
        ),
    ]
    return pd.DataFrame(
        {
            "validation_name": [check[0] for check in checks],
            "status": ["PASS" if check[1] else "FAIL" for check in checks],
            "details": [check[2] for check in checks],
        }
    )


def validate_outputs(dataframe: pd.DataFrame, validation_report: pd.DataFrame) -> None:
    assert INPUT_PATH.exists()
    assert ENGINEERED_PATH.exists()
    assert SUMMARY_PATH.exists()
    assert VALIDATION_PATH.exists()
    assert "rfm_score" in dataframe.columns
    assert "engagement_tier" in dataframe.columns
    assert "spend_quartile" in dataframe.columns
    assert not dataframe[ENGINEERED_COLUMNS].isna().any().any()
    assert (validation_report["status"] == "PASS").all()


def main() -> None:
    configure_logging()
    dataframe = pd.read_csv(INPUT_PATH)
    engineered = engineer_features(dataframe)
    summary_report = create_summary_report(engineered)
    validation_report = create_validation_report(engineered)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    engineered.to_csv(ENGINEERED_PATH, index=False)
    summary_report.to_csv(SUMMARY_PATH, index=False)
    validation_report.to_csv(VALIDATION_PATH, index=False)
    validate_outputs(engineered, validation_report)

    LOGGER.info("Transactions per month statistics:\n%s", engineered["transactions_per_month"].describe())
    LOGGER.info("Average spend per transaction statistics:\n%s", engineered["avg_spend_per_transaction"].describe())
    LOGGER.info("Lifetime value per month statistics:\n%s", engineered["lifetime_value_per_month"].describe())
    LOGGER.info("Engagement tier distribution:\n%s", engineered["engagement_tier"].value_counts().sort_index())
    LOGGER.info("Spend quartile distribution:\n%s", engineered["spend_quartile"].value_counts().sort_index())
    LOGGER.info(
        "RFM score min/max: %s / %s",
        engineered["rfm_score"].min(),
        engineered["rfm_score"].max(),
    )
    LOGGER.info("Missing values summary:\n%s", engineered[ENGINEERED_COLUMNS].isna().sum())
    print("Feature Engineering Pipeline completed successfully.")


if __name__ == "__main__":
    main()