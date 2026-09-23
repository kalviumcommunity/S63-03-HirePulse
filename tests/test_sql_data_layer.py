"""Integration tests for the SQL Views & Aggregation Layer assignment."""

from __future__ import annotations

import os

import pandas as pd
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://hirepulse@localhost:55432/hirepulse_sql",
)


@pytest.fixture(scope="module")
def connection():
    try:
        engine = create_engine(DATABASE_URL, future=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            yield connection
    except SQLAlchemyError as error:
        pytest.fail(f"Database connection failed: {error}")


def test_required_objects_exist(connection):
    inspector = inspect(connection)
    assert {"vw_active_customers", "vw_revenue_by_region"}.issubset(
        inspector.get_view_names()
    )
    assert "agg_daily_metrics" in inspector.get_table_names()


def test_active_customers_view_is_current_and_nonempty(connection):
    result = pd.read_sql(
        text("""
            SELECT customer_id, order_count_30d, revenue_30d, days_since_order
            FROM vw_active_customers
        """),
        connection,
    )
    assert not result.empty
    assert (result["order_count_30d"] > 0).all()
    assert (result["revenue_30d"] >= 0).all()
    assert (result["days_since_order"] >= 0).all()


def test_revenue_by_region_view_has_aggregated_values(connection):
    result = pd.read_sql(
        text("SELECT * FROM vw_revenue_by_region"),
        connection,
    )
    assert not result.empty
    assert result["region"].notna().all()
    assert (result["order_count"] > 0).all()
    assert (result["total_revenue"] > 0).all()
    assert (result["average_order_value"] > 0).all()


def test_daily_aggregate_has_rows_and_refresh_timestamps(connection):
    result = pd.read_sql(
        text("""
            SELECT aggregation_date, metric_name, metric_value,
                   row_count, updated_at
            FROM agg_daily_metrics
        """),
        connection,
    )
    assert not result.empty
    assert result["aggregation_date"].notna().all()
    assert (result["metric_name"] == "daily_completed_revenue").all()
    assert (result["metric_value"] >= 0).all()
    assert (result["row_count"] > 0).all()
    assert result["updated_at"].notna().all()