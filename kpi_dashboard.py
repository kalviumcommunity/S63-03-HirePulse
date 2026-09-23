"""Compute and render five current-vs-prior-month KPI cards."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "visualization_sales.csv"
SATISFACTION_PATH = ROOT / "data" / "customer_satisfaction.csv"
DEFAULT_DATABASE_URL = "postgresql+psycopg2://hirepulse@localhost:55432/hirepulse_sql"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
COLORS = {"green": "#10b981", "red": "#ef4444", "yellow": "#f59e0b"}


def month_bounds(as_of: date | None = None) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    anchor = pd.Timestamp(as_of or date.today()).normalize()
    current_start = anchor.replace(day=1)
    prior_start = current_start - pd.offsets.MonthBegin(1)
    next_start = current_start + pd.offsets.MonthBegin(1)
    return current_start, next_start, prior_start


def percentage_change(current: float, prior: float) -> float:
    if prior == 0:
        return 0.0 if current == 0 else float("inf")
    return (current - prior) / prior * 100


def get_trend_indicator(change_pct: float, metric_name: str) -> dict[str, str]:
    is_churn = metric_name.lower() == "churn rate"
    if change_pct > 2:
        status = "negative" if is_churn else "positive"
        arrow = "↑"
    elif change_pct < -2:
        status = "positive" if is_churn else "negative"
        arrow = "↓"
    else:
        status = "neutral"
        arrow = "→"
    return {"arrow": arrow, "status": status, "color": COLORS["green" if status == "positive" else "red" if status == "negative" else "yellow"]}


def _period_sum(frame: pd.DataFrame, date_column: str, value_column: str, start, end) -> float:
    mask = frame[date_column].ge(start) & frame[date_column].lt(end)
    return float(frame.loc[mask, value_column].sum())


def _period_mean(frame: pd.DataFrame, date_column: str, value_column: str, start, end) -> float:
    mask = frame[date_column].ge(start) & frame[date_column].lt(end)
    values = pd.to_numeric(frame.loc[mask, value_column], errors="coerce").dropna()
    return float(values.mean()) if not values.empty else 0.0


def _period_count(frame: pd.DataFrame, date_column: str, id_column: str, start, end) -> float:
    mask = frame[date_column].ge(start) & frame[date_column].lt(end)
    return float(frame.loc[mask, id_column].nunique())


def _churn_rate(orders: pd.DataFrame, current_start, current_end, prior_start, prior_end) -> float:
    valid = orders[orders["order_status"].eq("completed") & orders["order_amount"].gt(0)].copy()
    valid["order_date"] = pd.to_datetime(valid["order_date"])
    prior = set(valid.loc[valid["order_date"].between(prior_start, prior_end, inclusive="left"), "customer_id"])
    current = set(valid.loc[valid["order_date"].between(current_start, current_end, inclusive="left"), "customer_id"])
    return len(prior - current) / len(prior) * 100 if prior else 0.0


def calculate_kpis(engine: Engine, as_of: date | None = None) -> pd.DataFrame:
    current_start, current_end, prior_start = month_bounds(as_of)
    prior_end = current_start
    orders = pd.read_sql(text("SELECT customer_id, order_date, order_amount, order_status FROM orders"), engine)
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    logins = pd.read_sql(text("SELECT user_id, login_at FROM logins"), engine)
    logins["login_at"] = pd.to_datetime(logins["login_at"], utc=True).dt.tz_localize(None)
    sales = pd.read_csv(DATA_PATH, parse_dates=["order_date"])
    satisfaction = pd.read_csv(SATISFACTION_PATH, parse_dates=["rating_date"])
    current_values = {
        "Revenue": _period_sum(sales, "order_date", "order_amount", current_start, current_end),
        "Active Users": _period_count(logins, "login_at", "user_id", current_start, current_end),
        "AOV": _period_mean(sales, "order_date", "order_amount", current_start, current_end),
        "Churn Rate": _churn_rate(orders, current_start, current_end, prior_start, prior_end),
        "Satisfaction": _period_mean(satisfaction, "rating_date", "rating", current_start, current_end),
    }
    prior_values = {
        "Revenue": _period_sum(sales, "order_date", "order_amount", prior_start, prior_end),
        "Active Users": _period_count(logins, "login_at", "user_id", prior_start, prior_end),
        "AOV": _period_mean(sales, "order_date", "order_amount", prior_start, prior_end),
        "Churn Rate": _churn_rate(orders, prior_start, prior_end, prior_start - pd.offsets.MonthBegin(1), prior_start),
        "Satisfaction": _period_mean(satisfaction, "rating_date", "rating", prior_start, prior_end),
    }
    rows = []
    for metric in current_values:
        change = percentage_change(current_values[metric], prior_values[metric])
        trend = get_trend_indicator(change, metric)
        rows.append({"Metric": metric, "Current": current_values[metric], "Prior": prior_values[metric], "Change_Pct": change,
                     "Trend": f"{trend['arrow']} {trend['status']}", "Arrow": trend["arrow"], "Status": trend["status"], "Color": trend["color"],
                     "Change_Display": "N/A" if change == float("inf") else "0%" if change == 0 else f"{change:+.1f}%"})
    return pd.DataFrame(rows)


def format_value(metric: str, value: float) -> str:
    if metric in {"Revenue", "AOV"}:
        return f"${value:,.2f}"
    if metric == "Active Users":
        return f"{value:,.0f}"
    if metric == "Churn Rate":
        return f"{value:.1f}%"
    return f"{value:.2f}/5"


if __name__ == "__main__":
    result = calculate_kpis(create_engine(DATABASE_URL, future=True))
    print(result[["Metric", "Current", "Prior", "Change_Display", "Trend"]].to_string(index=False))