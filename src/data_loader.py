"""Reusable CSV loading functions."""

from pathlib import Path

import pandas as pd

from config import DATA_FILES


def _load_csv(name: str, path: Path | None = None) -> pd.DataFrame:
    """Load a project CSV with consistent parsing and useful errors."""
    file_path = path or DATA_FILES[name]
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    return pd.read_csv(file_path)


def load_candidates(path: Path | None = None) -> pd.DataFrame:
    return _load_csv("candidates", path)


def load_stages(path: Path | None = None) -> pd.DataFrame:
    return _load_csv("stages", path)


def load_interviews(path: Path | None = None) -> pd.DataFrame:
    return _load_csv("interviews", path)


def load_offers(path: Path | None = None) -> pd.DataFrame:
    return _load_csv("offers", path)


def load_onboarding(path: Path | None = None) -> pd.DataFrame:
    return _load_csv("onboarding", path)
