"""Data cleaning utilities used before analytics transformations."""

from collections.abc import Iterable

import pandas as pd


def clean_missing_values(
    frame: pd.DataFrame,
    fill_values: dict[str, object] | None = None,
) -> pd.DataFrame:
    """Return a copy with configured values filled and text nulls normalized."""
    cleaned = frame.copy()
    if fill_values:
        cleaned = cleaned.fillna(fill_values)
    text_columns = cleaned.select_dtypes(include="object").columns
    cleaned[text_columns] = cleaned[text_columns].fillna("")
    return cleaned


def remove_duplicates(frame: pd.DataFrame, subset: Iterable[str] | None = None) -> pd.DataFrame:
    """Remove duplicate rows, optionally using a business-key subset."""
    return frame.drop_duplicates(subset=list(subset) if subset else None).reset_index(drop=True)


def standardize_text(frame: pd.DataFrame, columns: Iterable[str] | None = None) -> pd.DataFrame:
    """Trim whitespace and normalize text casing without changing identifiers."""
    cleaned = frame.copy()
    selected = list(columns) if columns else list(cleaned.select_dtypes(include="object").columns)
    for column in selected:
        if column in cleaned.columns:
            cleaned[column] = cleaned[column].astype("string").str.strip()
    return cleaned


def convert_dates(frame: pd.DataFrame, columns: Iterable[str] | None = None) -> pd.DataFrame:
    """Convert date columns to pandas datetimes, coercing invalid values to NaT."""
    cleaned = frame.copy()
    selected = list(columns) if columns else [column for column in cleaned if column.endswith("_date")]
    for column in selected:
        if column in cleaned.columns:
            cleaned[column] = pd.to_datetime(cleaned[column], errors="coerce")
    return cleaned


def validate_schema(frame: pd.DataFrame, required_columns: Iterable[str]) -> None:
    """Raise a clear error when required columns are absent."""
    missing = sorted(set(required_columns) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
