import json
import logging
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "customer_segment_data.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"
METRICS_PATH = OUTPUT_DIR / "segment_metrics_report.csv"
PIVOT_PATH = OUTPUT_DIR / "segment_product_revenue_pivot.csv"
TOP_SEGMENTS_PATH = OUTPUT_DIR / "top_segments_report.csv"
INSIGHTS_PATH = OUTPUT_DIR / "segment_insights.json"
VALIDATION_PATH = OUTPUT_DIR / "segment_validation_report.csv"

LOGGER = logging.getLogger(__name__)
EXPECTED_TYPES = {"Enterprise", "SMB", "Startup"}
EXPECTED_PRODUCTS = {"Product_A", "Product_B", "Product_C"}


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def load_and_validate() -> pd.DataFrame:
    assert INPUT_PATH.exists()
    dataframe = pd.read_csv(INPUT_PATH)
    assert len(dataframe) >= 150
    assert dataframe["customer_id"].is_unique
    assert set(dataframe["customer_type"]) == EXPECTED_TYPES
    assert set(dataframe["product"]) == EXPECTED_PRODUCTS
    assert not dataframe.isna().any().any()
    assert (dataframe["revenue"] >= 0).all()
    assert dataframe["churn"].isin([0, 1]).all()
    return dataframe


def create_validation_report(
    dataframe: pd.DataFrame, pivot: pd.DataFrame, insights: dict[str, dict[str, object]]
) -> pd.DataFrame:
    checks = [
        ("row_count", len(dataframe) >= 150, "Dataset contains at least 150 rows"),
        (
            "customer_types",
            set(dataframe["customer_type"]) == EXPECTED_TYPES,
            "All Enterprise, SMB, and Startup customer types are present",
        ),
        (
            "products",
            set(dataframe["product"]) == EXPECTED_PRODUCTS,
            "All three expected products are present",
        ),
        ("null_check", not dataframe.isna().any().any(), "Dataset contains no null values"),
        ("pivot_created", pivot.shape == (3, 3), "Segment-product revenue pivot has shape 3x3"),
        ("insights_created", set(insights) == EXPECTED_TYPES, "Insights exist for every customer type"),
    ]
    return pd.DataFrame(
        {
            "validation_name": [check[0] for check in checks],
            "status": ["PASS" if check[1] else "FAIL" for check in checks],
            "details": [check[2] for check in checks],
        }
    )


def main() -> None:
    configure_logging()
    dataframe = load_and_validate()

    segment_metrics = (
        dataframe.groupby("customer_type")
        .agg({"churn": "mean", "revenue": "sum", "customer_id": "count"})
        .rename(
            columns={
                "churn": "churn_rate",
                "revenue": "total_revenue",
                "customer_id": "customer_count",
            }
        )
    )
    pivot = (
        dataframe.groupby(["customer_type", "product"])["revenue"]
        .sum()
        .unstack(fill_value=0)
        .reindex(index=sorted(EXPECTED_TYPES), columns=sorted(EXPECTED_PRODUCTS))
    )
    segment_metrics["churn_rank"] = segment_metrics["churn_rate"].rank(
        ascending=False, method="min"
    ).astype(int)
    segment_metrics["revenue_rank"] = segment_metrics["total_revenue"].rank(
        ascending=False, method="min"
    ).astype(int)
    top_segments = segment_metrics.sort_values("churn_rate", ascending=False).reset_index()

    insights = {
        "Enterprise": {
            "churn_rate": float(segment_metrics.loc["Enterprise", "churn_rate"]),
            "total_revenue": float(segment_metrics.loc["Enterprise", "total_revenue"]),
            "insight": "Healthy segment with strong revenue and low churn",
        },
        "SMB": {
            "churn_rate": float(segment_metrics.loc["SMB", "churn_rate"]),
            "total_revenue": float(segment_metrics.loc["SMB", "total_revenue"]),
            "insight": "Highest churn segment requiring intervention",
        },
        "Startup": {
            "churn_rate": float(segment_metrics.loc["Startup", "churn_rate"]),
            "total_revenue": float(segment_metrics.loc["Startup", "total_revenue"]),
            "insight": "Moderate churn with growth potential",
        },
    }
    validation = create_validation_report(dataframe, pivot, insights)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    segment_metrics.reset_index().to_csv(METRICS_PATH, index=False)
    pivot.to_csv(PIVOT_PATH)
    top_segments.to_csv(TOP_SEGMENTS_PATH, index=False)
    INSIGHTS_PATH.write_text(json.dumps(insights, indent=2) + "\n", encoding="utf-8")
    validation.to_csv(VALIDATION_PATH, index=False)

    assert pivot.shape == (3, 3)
    assert len(segment_metrics) == 3
    assert METRICS_PATH.exists()
    assert PIVOT_PATH.exists()
    assert TOP_SEGMENTS_PATH.exists()
    assert INSIGHTS_PATH.exists()
    assert VALIDATION_PATH.exists()
    assert (validation["status"] == "PASS").all()

    LOGGER.info("Dataset Shape: %s", dataframe.shape)
    LOGGER.info("Segment Metrics:\n%s", segment_metrics.to_string())
    LOGGER.info("Top Segments By Churn:\n%s", top_segments.to_string(index=False))
    LOGGER.info("Validation Report:\n%s", validation.to_string(index=False))
    print("Segment Aggregation Workflow completed successfully.")


if __name__ == "__main__":
    main()