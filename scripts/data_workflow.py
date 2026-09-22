"""Production-style ingestion, processing, and output workflow."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DATA_FILES, OUTPUTS_DIR  # noqa: E402
from data_cleaning import (  # noqa: E402
    clean_missing_values,
    convert_dates,
    remove_duplicates,
    standardize_text,
    validate_schema,
)
from data_loader import (  # noqa: E402
    load_candidates,
    load_interviews,
    load_onboarding,
    load_offers,
    load_stages,
)
from data_validation import SCHEMAS  # noqa: E402
from feature_engineering import build_candidate_features  # noqa: E402

INPUT_FILE = DATA_FILES["candidates"]
OUTPUT_FILE = OUTPUTS_DIR / "processed_candidates.csv"
LOG_FILE = OUTPUTS_DIR / "data_workflow.log"
MIN_ROWS_REQUIRED = 1

SOURCE_LOADERS = {
    "candidates": load_candidates,
    "stages": load_stages,
    "interviews": load_interviews,
    "offers": load_offers,
    "onboarding": load_onboarding,
}


def _configure_logging() -> logging.Logger:
    """Configure workflow logging and return the module logger.

    Inputs:
        None. The log destination is configured by ``LOG_FILE``.
    Outputs:
        A configured :class:`logging.Logger` instance.
    Assumptions:
        The project output directory can be created by the running user.
    Possible errors:
        ``OSError`` can be raised when the log directory or file is not writable.
    """
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        force=True,
    )
    return logging.getLogger(__name__)


def ingest_data() -> dict[str, pd.DataFrame]:
    """Load every relational source table required by the analytics pipeline.

    Inputs:
        None. CSV locations come from ``src.config.DATA_FILES``.
    Outputs:
        A mapping of source name to loaded pandas DataFrame.
    Assumptions:
        The workflow is run from a checkout containing the project's ``data`` directory.
    Possible errors:
        Raises ``FileNotFoundError`` for a missing source, ``ValueError`` for an
        empty source, and propagates unexpected CSV/parser errors.
    """
    logger = logging.getLogger(__name__)
    frames: dict[str, pd.DataFrame] = {}
    for name, loader in SOURCE_LOADERS.items():
        frame = loader()
        if frame.empty or len(frame) < MIN_ROWS_REQUIRED:
            error = f"Input dataset is empty: {name} ({DATA_FILES[name]})"
            logger.error(error)
            raise ValueError(error)
        frames[name] = frame
        logger.info("File loaded: %s; rows ingested: %d", DATA_FILES[name], len(frame))
    return frames


def process_data(df: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Clean source tables and build the candidate-level analytical dataset.

    Inputs:
        ``df``: Mapping containing the five DataFrames returned by ``ingest_data``.
    Outputs:
        A candidate-level DataFrame with application, offer, joining, and hiring
        duration features.
    Assumptions:
        Each source follows the schema declared in ``src.data_validation.SCHEMAS``
        and uses ``candidate_id`` as its relational key.
    Possible errors:
        Raises ``ValueError`` for missing sources or invalid schemas, and
        propagates transformation errors from pandas or feature engineering.
    """
    logger = logging.getLogger(__name__)
    if not isinstance(df, dict) or set(df) != set(SCHEMAS):
        raise ValueError(f"Expected source datasets: {', '.join(SCHEMAS)}")

    cleaned: dict[str, pd.DataFrame] = {}
    for name, frame in df.items():
        validate_schema(frame, SCHEMAS[name])
        # Normalize text and dates before joins so equivalent source values match reliably.
        prepared = standardize_text(frame)
        prepared = convert_dates(prepared)
        prepared = clean_missing_values(prepared)
        cleaned[name] = remove_duplicates(prepared)

    result = build_candidate_features(
        cleaned["candidates"],
        cleaned["stages"],
        cleaned["offers"],
        cleaned["onboarding"],
    )
    logger.info("Rows processed: %d", len(result))
    return result


def output_results(df: pd.DataFrame, output_path: Path = OUTPUT_FILE) -> Path:
    """Write processed analytical results to a CSV file.

    Inputs:
        ``df``: Processed candidate-level DataFrame.
        ``output_path``: Destination path for the exported CSV.
    Outputs:
        The resolved ``Path`` written to disk.
    Assumptions:
        The output is a tabular CSV consumed by downstream analytics steps.
    Possible errors:
        Raises ``ValueError`` for an empty result and ``OSError`` or pandas
        exceptions when the destination cannot be written.
    """
    logger = logging.getLogger(__name__)
    if df.empty:
        raise ValueError("Cannot write an empty processed dataset")
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(destination, index=False)
    logger.info("Output generated: %s; rows written: %d", destination, len(df))
    return destination


def main() -> int:
    """Run the workflow from ingestion through output and print a summary.

    Inputs:
        None. Runtime configuration is provided by the module constants.
    Outputs:
        Returns ``0`` on success and ``1`` after logging a handled failure.
    Assumptions:
        Input files and their schemas are available in the repository checkout.
    Possible errors:
        Handles missing files, empty datasets, invalid schemas, and unexpected
        exceptions by logging the error and returning a non-zero status.
    """
    logger = _configure_logging()
    try:
        ingested = ingest_data()
        processed = process_data(ingested)
        destination = output_results(processed, OUTPUT_FILE)
    except FileNotFoundError as error:
        logger.error("File not found: %s", error)
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except ValueError as error:
        logger.error("Data validation failed: %s", error)
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except Exception as error:  # Keep the CLI from hiding operational failures.
        logger.exception("Unexpected workflow error: %s", error)
        print(f"ERROR: Unexpected workflow error: {error}", file=sys.stderr)
        return 1

    print("✓ Data successfully processed")
    print(f"✓ Rows processed: {len(processed)}")
    print(f"✓ Output saved to: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())