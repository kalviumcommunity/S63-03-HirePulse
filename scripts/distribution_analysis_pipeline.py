import logging
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "customer_distribution_data.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"
SUMMARY_PATH = OUTPUT_DIR / "distribution_summary_report.csv"
STATISTICS_PATH = OUTPUT_DIR / "distribution_statistics_report.csv"
VALIDATION_PATH = OUTPUT_DIR / "distribution_validation_report.csv"
HISTOGRAM_PATH = OUTPUT_DIR / "revenue_histogram.png"
KDE_PATH = OUTPUT_DIR / "revenue_kde.png"

LOGGER = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def create_plots(revenue: pd.Series) -> None:
    plt.figure(figsize=(10, 6))
    plt.hist(revenue, bins=30, color="#2563eb", edgecolor="white")
    plt.title("Revenue Distribution")
    plt.xlabel("Revenue")
    plt.ylabel("Customer Count")
    plt.tight_layout()
    plt.savefig(HISTOGRAM_PATH, dpi=150)
    plt.close()

    density = stats.gaussian_kde(revenue.to_numpy())
    x_values = np.linspace(revenue.min(), revenue.max(), 500)
    plt.figure(figsize=(10, 6))
    plt.plot(x_values, density(x_values), color="#dc2626", linewidth=2)
    plt.fill_between(x_values, density(x_values), alpha=0.2, color="#dc2626")
    plt.title("Revenue Kernel Density Estimate")
    plt.xlabel("Revenue")
    plt.ylabel("Density")
    plt.tight_layout()
    plt.savefig(KDE_PATH, dpi=150)
    plt.close()


def create_validation_report(
    dataframe: pd.DataFrame, skewness: float, kurtosis: float
) -> pd.DataFrame:
    checks = [
        (
            "revenue_column_exists",
            "revenue" in dataframe.columns,
            "Revenue column is present",
        ),
        (
            "revenue_values_positive",
            dataframe["revenue"].gt(0).all(),
            "All revenue values are greater than zero",
        ),
        (
            "no_missing_values",
            not dataframe[["customer_id", "revenue", "customer_segment"]].isna().any().any(),
            "No missing values exist in required columns",
        ),
        ("histogram_generated", HISTOGRAM_PATH.exists(), "Revenue histogram file exists"),
        ("kde_generated", KDE_PATH.exists(), "Revenue KDE file exists"),
        (
            "skewness_calculated",
            isinstance(skewness, (float, np.floating)) and np.isfinite(skewness),
            "Skewness is a finite numeric value",
        ),
        (
            "kurtosis_calculated",
            isinstance(kurtosis, (float, np.floating)) and np.isfinite(kurtosis),
            "Kurtosis is a finite numeric value",
        ),
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
    dataframe = pd.read_csv(INPUT_PATH)
    assert len(dataframe) >= 100
    assert dataframe["revenue"].gt(0).all()
    assert not dataframe[["customer_id", "revenue", "customer_segment"]].isna().any().any()

    revenue = dataframe["revenue"]
    descriptive_statistics = {
        "mean": revenue.mean(),
        "median": revenue.median(),
        "min": revenue.min(),
        "max": revenue.max(),
        "std": revenue.std(),
    }
    skewness = stats.skew(dataframe["revenue"])
    kurtosis = stats.kurtosis(dataframe["revenue"])
    if abs(skewness) > 1:
        interpretation = "Highly Skewed"
    elif abs(skewness) > 0.5:
        interpretation = "Moderately Skewed"
    else:
        interpretation = "Approximately Symmetric"

    LOGGER.info("Descriptive statistics:\n%s", pd.Series(descriptive_statistics))
    LOGGER.info("Skewness: %.6f", skewness)
    LOGGER.info("Kurtosis: %.6f", kurtosis)
    LOGGER.info("Interpretation: %s", interpretation)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    create_plots(revenue)
    segment_summary = (
        dataframe.groupby("customer_segment", observed=True)["revenue"]
        .agg(count="count", mean_revenue="mean", median_revenue="median", std_revenue="std")
        .reset_index()
    )
    statistics_report = pd.DataFrame(
        {
            "metric": ["mean", "median", "std", "min", "max", "skewness", "kurtosis"],
            "value": [
                descriptive_statistics["mean"],
                descriptive_statistics["median"],
                descriptive_statistics["std"],
                descriptive_statistics["min"],
                descriptive_statistics["max"],
                skewness,
                kurtosis,
            ],
        }
    )
    validation_report = create_validation_report(dataframe, skewness, kurtosis)
    segment_summary.to_csv(SUMMARY_PATH, index=False)
    statistics_report.to_csv(STATISTICS_PATH, index=False)
    validation_report.to_csv(VALIDATION_PATH, index=False)

    assert SUMMARY_PATH.exists()
    assert STATISTICS_PATH.exists()
    assert VALIDATION_PATH.exists()
    assert HISTOGRAM_PATH.exists()
    assert KDE_PATH.exists()
    assert np.isfinite(skewness) and np.isfinite(kurtosis)
    assert (validation_report["status"] == "PASS").all()

    LOGGER.info("Segment comparison:\n%s", segment_summary.to_string(index=False))
    LOGGER.info("Validation results:\n%s", validation_report.to_string(index=False))
    print("Distribution Analysis Workflow completed successfully.")


if __name__ == "__main__":
    main()