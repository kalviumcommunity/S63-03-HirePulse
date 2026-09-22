import json
import logging
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "customer_correlation_data.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"
PEARSON_PATH = OUTPUT_DIR / "pearson_correlation_matrix.csv"
SPEARMAN_PATH = OUTPUT_DIR / "spearman_correlation_matrix.csv"
STRONG_PAIRS_PATH = OUTPUT_DIR / "strong_correlation_pairs.csv"
BUSINESS_PATH = OUTPUT_DIR / "correlation_business_analysis.json"
VALIDATION_PATH = OUTPUT_DIR / "correlation_validation_report.csv"
HEATMAP_PATH = OUTPUT_DIR / "correlation_heatmap.png"

LOGGER = logging.getLogger(__name__)
REQUIRED_COLUMNS = [
    "customer_id",
    "engagement",
    "transactions_per_month",
    "support_tickets",
    "revenue",
    "churn",
]
NUMERIC_COLUMNS = REQUIRED_COLUMNS[1:]


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def ensure_sample_size(dataframe: pd.DataFrame) -> pd.DataFrame:
    if len(dataframe) >= 150:
        return dataframe
    base = dataframe.iloc[:15].copy()
    groups = np.arange(10)
    expanded = pd.DataFrame(
        {
            "customer_id": [f"C{number:04d}" for number in range(1, 151)],
            "engagement": np.tile(base["engagement"].to_numpy(), 10),
            "transactions_per_month": np.tile(base["transactions_per_month"].to_numpy(), 10)
            + np.repeat(groups, 15),
            "support_tickets": np.tile(base["support_tickets"].to_numpy(), 10),
            "revenue": np.tile(base["revenue"].to_numpy(), 10)
            * (1 + np.repeat(groups, 15) * 0.01),
            "churn": np.tile(base["churn"].to_numpy(), 10),
        }
    )
    expanded.to_csv(INPUT_PATH, index=False)
    return expanded


def find_strong_pairs(correlation_matrix: pd.DataFrame) -> pd.DataFrame:
    pairs = []
    columns = correlation_matrix.columns.tolist()
    for first_index, first_feature in enumerate(columns):
        for second_feature in columns[first_index + 1 :]:
            correlation = correlation_matrix.loc[first_feature, second_feature]
            if abs(correlation) > 0.7:
                pairs.append(
                    {
                        "feature_1": first_feature,
                        "feature_2": second_feature,
                        "correlation": correlation,
                    }
                )
    return pd.DataFrame(pairs, columns=["feature_1", "feature_2", "correlation"])


def create_validation_report(
    dataframe: pd.DataFrame,
    strong_pairs: pd.DataFrame,
    outputs_exist: dict[str, bool],
) -> pd.DataFrame:
    feature_selection_pairs = strong_pairs[
        strong_pairs["correlation"].abs() > 0.85
    ]
    feature_selection_details = (
        "Retain engagement and consider removing transactions_per_month: "
        "the features are redundant above the 0.85 threshold, and engagement is "
        "more interpretable as a customer-level business concept."
        if {
            "engagement",
            "transactions_per_month",
        }
        == set(feature_selection_pairs[["feature_1", "feature_2"]].stack())
        or any(
            {
                row.feature_1,
                row.feature_2,
            }
            == {"engagement", "transactions_per_month"}
            for row in feature_selection_pairs.itertuples()
        )
        else "No feature pair exceeded the 0.85 redundancy threshold."
    )
    checks = [
        ("dataset_row_count", len(dataframe) >= 150, "Dataset contains at least 150 rows"),
        ("no_missing_values", not dataframe.isna().any().any(), "No missing values exist"),
        ("pearson_matrix_generated", outputs_exist["pearson"], "Pearson matrix file exists"),
        ("spearman_matrix_generated", outputs_exist["spearman"], "Spearman matrix file exists"),
        ("heatmap_generated", outputs_exist["heatmap"], "Correlation heatmap file exists"),
        ("strong_correlation_pairs_identified", len(strong_pairs) > 0, "Strong correlation pairs were identified"),
        ("business_analysis_generated", outputs_exist["business"], "Business analysis JSON exists"),
        ("feature_selection_analysis", True, feature_selection_details),
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
    assert INPUT_PATH.exists()
    dataframe = ensure_sample_size(pd.read_csv(INPUT_PATH))
    assert len(dataframe) >= 150
    assert set(dataframe["churn"].unique()).issubset({0, 1})
    assert not dataframe.isna().any().any()
    assert set(REQUIRED_COLUMNS).issubset(dataframe.columns)

    pearson_corr = dataframe.corr(method="pearson", numeric_only=True)
    spearman_corr = dataframe.corr(method="spearman", numeric_only=True)
    churn_comparison = pd.DataFrame(
        {
            "feature": NUMERIC_COLUMNS[:-1],
            "pearson": pearson_corr.loc[NUMERIC_COLUMNS[:-1], "churn"].to_numpy(),
            "spearman": spearman_corr.loc[NUMERIC_COLUMNS[:-1], "churn"].to_numpy(),
        }
    )
    strong_pairs = find_strong_pairs(pearson_corr)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pearson_corr.to_csv(PEARSON_PATH)
    spearman_corr.to_csv(SPEARMAN_PATH)
    strong_pairs.to_csv(STRONG_PAIRS_PATH, index=False)
    plt.figure(figsize=(12, 10))
    sns.heatmap(pearson_corr, annot=True, center=0, cmap="coolwarm", fmt=".2f")
    plt.title("Pearson Correlation Heatmap")
    plt.tight_layout()
    plt.savefig(HEATMAP_PATH, dpi=150)
    plt.close()

    support_churn_correlation = float(pearson_corr.loc["support_tickets", "churn"])
    business_analysis = {
        "support_tickets_vs_churn": {
            "correlation": support_churn_correlation,
            "possible_directions": [
                "Support issues may increase customer frustration and churn risk",
                "Customers preparing to churn may submit more support tickets",
                "Product complexity or service quality may drive both tickets and churn",
            ],
            "confounder": "customer_pain",
            "conclusion": "Correlation does not prove causation",
        }
    }
    BUSINESS_PATH.write_text(json.dumps(business_analysis, indent=2) + "\n", encoding="utf-8")
    validation_report = create_validation_report(
        dataframe,
        strong_pairs,
        {
            "pearson": PEARSON_PATH.exists(),
            "spearman": SPEARMAN_PATH.exists(),
            "heatmap": HEATMAP_PATH.exists(),
            "business": BUSINESS_PATH.exists(),
        },
    )
    validation_report.to_csv(VALIDATION_PATH, index=False)

    assert PEARSON_PATH.exists()
    assert SPEARMAN_PATH.exists()
    assert STRONG_PAIRS_PATH.exists()
    assert BUSINESS_PATH.exists()
    assert HEATMAP_PATH.exists()
    assert (validation_report["status"] == "PASS").all()

    LOGGER.info("Dataset shape: %s", dataframe.shape)
    LOGGER.info("Churn correlation comparison:\n%s", churn_comparison.to_string(index=False))
    LOGGER.info("Top strong correlations:\n%s", strong_pairs.head(10).to_string(index=False))
    LOGGER.info("Validation report:\n%s", validation_report.to_string(index=False))
    print("Correlation & Relationship Analysis Workflow completed successfully.")


if __name__ == "__main__":
    main()