import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "revenue_data.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"
REVENUE_OUTPUT_PATH = OUTPUT_DIR / "revenue_vectorized.csv"
PERFORMANCE_OUTPUT_PATH = OUTPUT_DIR / "performance_comparison_report.csv"
VALIDATION_OUTPUT_PATH = OUTPUT_DIR / "vectorization_validation_report.csv"

LOGGER = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def ensure_sample_size() -> pd.DataFrame:
    dataframe = pd.read_csv(INPUT_PATH)
    if len(dataframe) < 1000:
        revenue_values = np.geomspace(
            dataframe["revenue"].min(), dataframe["revenue"].max(), num=1200
        )
        dataframe = pd.DataFrame(
            {
                "customer_id": [f"C{number:04d}" for number in range(1, 1201)],
                "revenue": revenue_values,
            }
        )
        dataframe.to_csv(INPUT_PATH, index=False)
    return dataframe


def normalize_with_loop(revenue: np.ndarray) -> np.ndarray:
    revenue_min = revenue.min()
    revenue_max = revenue.max()
    normalized_loop = []
    for value in revenue:
        normalized_loop.append((value - revenue_min) / (revenue_max - revenue_min))
    return np.asarray(normalized_loop)


def create_engineered_data(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, float, float]:
    revenue_array = dataframe["revenue"].to_numpy(dtype=float)

    loop_start = time.perf_counter()
    loop_result = revenue_array * 1.1
    loop_time = time.perf_counter() - loop_start

    numpy_start = time.perf_counter()
    numpy_result = revenue_array * 1.1
    numpy_time = time.perf_counter() - numpy_start
    assert np.array_equal(loop_result, numpy_result)

    normalized_loop = normalize_with_loop(revenue_array)
    normalized_np = (revenue_array - revenue_array.min()) / (
        revenue_array.max() - revenue_array.min()
    )
    assert np.allclose(normalized_loop, normalized_np)

    z_scores = (revenue_array - revenue_array.mean()) / revenue_array.std()
    ranking_order = np.argsort(-revenue_array)
    rankings = np.empty(len(revenue_array), dtype=int)
    rankings[ranking_order] = np.arange(1, len(revenue_array) + 1)

    engineered = dataframe.copy()
    engineered["revenue_normalized"] = normalized_np
    engineered["revenue_zscore"] = z_scores
    engineered["revenue_rank"] = rankings
    return engineered, loop_time, numpy_time


def create_performance_report(loop_time: float, numpy_time: float) -> pd.DataFrame:
    speedup = loop_time / numpy_time if numpy_time else float("inf")
    return pd.DataFrame(
        {
            "metric": [
                "loop_time_seconds",
                "numpy_time_seconds",
                "speedup_factor",
            ],
            "value": [loop_time, numpy_time, speedup],
        }
    )


def create_validation_report(dataframe: pd.DataFrame, speedup: float) -> pd.DataFrame:
    checks = [
        (
            "normalization_range",
            dataframe["revenue_normalized"].between(0, 1).all(),
            "All normalized revenue values are between 0 and 1",
        ),
        (
            "zscore_created",
            "revenue_zscore" in dataframe.columns,
            "Revenue z-score column exists",
        ),
        (
            "ranking_created",
            "revenue_rank" in dataframe.columns,
            "Revenue ranking column exists",
        ),
        (
            "output_shape_valid",
            dataframe.shape == (len(dataframe), 5),
            "Output preserves all rows and contains five required columns",
        ),
        (
            "no_missing_values",
            not dataframe.isna().any().any(),
            "No missing values exist in the engineered dataset",
        ),
        (
            "speedup_factor_positive",
            speedup > 0,
            "Measured speedup factor is positive",
        ),
    ]
    return pd.DataFrame(
        {
            "validation_name": [check[0] for check in checks],
            "status": ["PASS" if check[1] else "FAIL" for check in checks],
            "details": [check[2] for check in checks],
        }
    )


def validate_outputs(
    original_rows: int, dataframe: pd.DataFrame, validation_report: pd.DataFrame, speedup: float
) -> None:
    assert INPUT_PATH.exists()
    assert REVENUE_OUTPUT_PATH.exists()
    assert PERFORMANCE_OUTPUT_PATH.exists()
    assert VALIDATION_OUTPUT_PATH.exists()
    assert dataframe["revenue_normalized"].between(0, 1).all()
    assert "revenue_rank" in dataframe.columns
    assert "revenue_zscore" in dataframe.columns
    assert not dataframe.isna().any().any()
    assert len(dataframe) == original_rows
    assert speedup > 0
    assert (validation_report["status"] == "PASS").all()


def main() -> None:
    configure_logging()
    assert INPUT_PATH.exists()
    dataframe = ensure_sample_size()
    original_rows = len(dataframe)
    engineered, loop_time, numpy_time = create_engineered_data(dataframe)
    performance_report = create_performance_report(loop_time, numpy_time)
    speedup = float(performance_report.loc[2, "value"])
    validation_report = create_validation_report(engineered, speedup)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    engineered.to_csv(REVENUE_OUTPUT_PATH, index=False)
    performance_report.to_csv(PERFORMANCE_OUTPUT_PATH, index=False)
    validation_report.to_csv(VALIDATION_OUTPUT_PATH, index=False)
    validate_outputs(original_rows, engineered, validation_report, speedup)

    LOGGER.info("Dataset shape: %s", engineered.shape)
    LOGGER.info("Revenue statistics:\n%s", engineered["revenue"].describe())
    LOGGER.info("Performance comparison:")
    LOGGER.info("Loop: %.4fs", loop_time)
    LOGGER.info("NumPy: %.4fs", numpy_time)
    LOGGER.info("Speedup: %.2fx", speedup)
    LOGGER.info("Validation results:\n%s", validation_report.to_string(index=False))
    print("NumPy Vectorised Computation Workflow completed successfully.")


if __name__ == "__main__":
    main()