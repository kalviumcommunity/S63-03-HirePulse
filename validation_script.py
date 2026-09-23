"""Validate SQL-based business insights against equivalent pandas calculations."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError


ROOT = Path(__file__).resolve().parent
DEFAULT_DATABASE_URL = "postgresql+psycopg2://hirepulse@localhost:55432/hirepulse_sql"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
REPORT_PATH = ROOT / "validation_report.csv"


SQL_QUERIES = {
    "Active Users (30-day)": """
        SELECT COUNT(DISTINCT user_id)::double precision AS metric_value
        FROM logins
        WHERE login_at >= CURRENT_DATE - INTERVAL '30 days'
          AND login_at < CURRENT_DATE + INTERVAL '1 day'
    """,
    "Average Order Value": """
        SELECT AVG(order_amount)::double precision AS metric_value
        FROM orders
    """,
    "Monthly Customer Churn": """
        WITH month_bounds AS (
            SELECT date_trunc('month', CURRENT_DATE)::date AS current_month_start,
                   (date_trunc('month', CURRENT_DATE) - INTERVAL '1 month')::date AS previous_month_start
        ),
        previous_month AS (
            SELECT customer_id
            FROM orders, month_bounds
            WHERE order_status = 'completed'
              AND order_amount > 0
              AND order_date >= previous_month_start
              AND order_date < current_month_start
            GROUP BY customer_id
            HAVING SUM(order_amount) > 0
        ),
        current_month AS (
            SELECT DISTINCT customer_id
            FROM orders, month_bounds
            WHERE order_status = 'completed'
              AND order_amount > 0
              AND order_date >= current_month_start
              AND order_date < current_month_start + INTERVAL '1 month'
        )
        SELECT COUNT(*)::double precision AS metric_value
        FROM previous_month AS previous
        LEFT JOIN current_month AS current USING (customer_id)
        WHERE current.customer_id IS NULL
    """,
}


def _safe_pct_difference(sql_value: float, python_value: float) -> float:
    if sql_value == 0:
        return 0.0 if python_value == 0 else float("inf")
    return abs(python_value - sql_value) / abs(sql_value) * 100


def _calculate_python_metrics(connection) -> dict[str, float]:
    today = pd.Timestamp(
        pd.read_sql(text("SELECT CURRENT_DATE AS today"), connection).iloc[0]["today"]
    ).normalize()
    logins = pd.read_sql(
        text("SELECT user_id, login_at FROM logins"), connection
    )
    orders = pd.read_sql(
        text("SELECT customer_id, order_date, order_amount, order_status FROM orders"),
        connection,
    )

    login_times = pd.to_datetime(logins["login_at"], utc=True)
    cutoff = today.tz_localize("UTC") - pd.Timedelta(days=30)
    window_end = today.tz_localize("UTC") + pd.Timedelta(days=1)
    recent_logins = login_times.ge(cutoff) & login_times.lt(window_end)
    active_user_ids = int(logins.loc[recent_logins, "user_id"].nunique()) if not logins.empty else 0

    order_amounts = pd.to_numeric(orders["order_amount"], errors="coerce")
    average_order_value = float(order_amounts.mean()) if order_amounts.notna().any() else 0.0

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    orders["order_amount"] = order_amounts
    completed = orders[
        orders["order_status"].eq("completed")
        & orders["order_amount"].gt(0)
        & orders["order_date"].notna()
    ]
    current_month_start = today.replace(day=1)
    previous_month_start = current_month_start - pd.offsets.MonthBegin(1)
    previous = completed[
        completed["order_date"].ge(previous_month_start)
        & completed["order_date"].lt(current_month_start)
    ]
    current = completed[
        completed["order_date"].ge(current_month_start)
        & completed["order_date"].lt(current_month_start + pd.offsets.MonthBegin(1))
    ]
    previous_spenders = set(previous.groupby("customer_id")["order_amount"].sum().loc[lambda values: values.gt(0)].index)
    current_customers = set(current["customer_id"])
    churn = len(previous_spenders - current_customers)

    return {
        "Active Users (30-day)": float(active_user_ids),
        "Average Order Value": average_order_value,
        "Monthly Customer Churn": float(churn),
    }


def validate_metrics(engine: Engine, tolerance_pct: float = 0.1) -> pd.DataFrame:
    """Compare SQL and pandas metrics and return a validation report DataFrame."""
    timestamp = datetime.now(timezone.utc).isoformat()
    with engine.connect() as connection:
        python_results = _calculate_python_metrics(connection)
        rows = []
        for metric, query in SQL_QUERIES.items():
            sql_result = pd.read_sql(text(query), connection).iloc[0]["metric_value"]
            sql_value = float(sql_result) if pd.notna(sql_result) else 0.0
            python_value = python_results[metric]
            difference = abs(sql_value - python_value)
            metric_tolerance = tolerance_pct if metric == "Average Order Value" else 0.0
            pct_difference = _safe_pct_difference(sql_value, python_value)
            status = "PASS" if (
                pct_difference <= metric_tolerance
                if metric == "Average Order Value"
                else difference == 0
            ) else "FAIL"
            rows.append({
                "Metric": metric,
                "SQL": sql_value,
                "Python": python_value,
                "Difference": difference,
                "Pct_Difference": pct_difference,
                "Tolerance": metric_tolerance,
                "Status": status,
                "Timestamp": timestamp,
            })
    report = pd.DataFrame(rows)
    report.to_csv(REPORT_PATH, index=False)
    return report


def main() -> int:
    print("SQL-BASED INSIGHT VALIDATION")
    print("=" * 90)
    try:
        engine = create_engine(DATABASE_URL, future=True)
        report = validate_metrics(engine)
        print(report.to_string(index=False))
        print(f"\nReport saved to: {REPORT_PATH}")
        return 0 if report["Status"].eq("PASS").all() else 1
    except (SQLAlchemyError, ValueError, KeyError) as error:
        print(f"ERROR: validation failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())