"""Demonstrate the SQL Views & Aggregation Layer against PostgreSQL."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError


ROOT = Path(__file__).resolve().parent
DEFAULT_DATABASE_URL = "postgresql+psycopg2://hirepulse@localhost:55432/hirepulse_sql"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def verify_objects(connection) -> None:
    """Fail clearly unless all three required data-layer objects exist."""
    inspector = inspect(connection)
    views = set(inspector.get_view_names())
    tables = set(inspector.get_table_names())
    required_views = {"vw_active_customers", "vw_revenue_by_region"}
    if not required_views.issubset(views):
        raise RuntimeError(f"Missing views: {sorted(required_views - views)}")
    if "agg_daily_metrics" not in tables:
        raise RuntimeError("Missing table: agg_daily_metrics")


def main() -> int:
    print("SQL VIEWS & AGGREGATION LAYER")
    print("=" * 60)
    print(f"Database URL: {DATABASE_URL}")

    try:
        engine = create_engine(DATABASE_URL, future=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            verify_objects(connection)

            print("\n1. ACTIVE CUSTOMERS")
            print("-" * 60)
            active = pd.read_sql(
                text("""
                    SELECT customer_id, customer_name, revenue_30d, days_since_order
                    FROM vw_active_customers
                    WHERE order_count_30d > 0
                    ORDER BY revenue_30d DESC, customer_id
                """),
                connection,
            )
            print(active.to_string(index=False))

            print("\n2. REVENUE BY REGION")
            print("-" * 60)
            regional = pd.read_sql(
                text("""
                    SELECT region, country, customer_count, order_count,
                           total_revenue, average_order_value
                    FROM vw_revenue_by_region
                    ORDER BY total_revenue DESC, region, country
                    LIMIT 20
                """),
                connection,
            )
            print(regional.to_string(index=False))

            print("\n3. RECENT DAILY METRICS")
            print("-" * 60)
            daily = pd.read_sql(
                text("""
                    SELECT aggregation_date, metric_name, metric_value,
                           row_count, updated_at
                    FROM agg_daily_metrics
                    ORDER BY aggregation_date DESC
                    LIMIT 10
                """),
                connection,
            )
            print(daily.to_string(index=False))

            print("\n4. ACTIVE REVENUE BY SEGMENT")
            print("-" * 60)
            segment = pd.read_sql(
                text("""
                    SELECT segment,
                           COUNT(*) AS customer_count,
                           SUM(revenue_30d) AS total_segment_revenue,
                           AVG(revenue_30d) AS avg_customer_revenue
                    FROM vw_active_customers
                    GROUP BY segment
                    ORDER BY total_segment_revenue DESC, segment
                """),
                connection,
            )
            print(segment.to_string(index=False))

            print("\nVERIFICATION")
            print("-" * 60)
            print("All three data-layer objects are queryable.")
            print(f"Active-customer rows: {len(active)}")
            print(f"Regional rows: {len(regional)}")
            print(f"Daily-metric rows returned: {len(daily)}")
        return 0
    except (SQLAlchemyError, RuntimeError, ValueError) as error:
        print(f"ERROR: database demonstration failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())