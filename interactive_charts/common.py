"""Shared data loading and Plotly helpers for the interactive chart assignment."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "visualization_sales.csv"


def load_orders() -> pd.DataFrame:
    frame = pd.read_csv(DATA_PATH, parse_dates=["order_date"])
    required = {"order_id", "order_date", "product_line", "order_amount", "marketing_spend"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    return frame


def currency(value: float) -> str:
    return f"${value:,.2f}"