"""Tests for KPI period calculations and business trend semantics."""

from datetime import date

from sqlalchemy import create_engine

from kpi_dashboard import calculate_kpis, get_trend_indicator, month_bounds


def test_month_bounds_crosses_year_boundary():
    current, next_month, prior = month_bounds(date(2027, 1, 15))
    assert current.strftime("%Y-%m-%d") == "2027-01-01"
    assert next_month.strftime("%Y-%m-%d") == "2027-02-01"
    assert prior.strftime("%Y-%m-%d") == "2026-12-01"


def test_trend_semantics_include_churn_inversion():
    assert get_trend_indicator(5, "Revenue")["status"] == "positive"
    assert get_trend_indicator(-5, "Revenue")["status"] == "negative"
    assert get_trend_indicator(0, "Revenue")["status"] == "neutral"
    assert get_trend_indicator(-5, "Churn Rate")["status"] == "positive"
    assert get_trend_indicator(5, "Churn Rate")["status"] == "negative"


def test_live_kpis_have_five_runtime_metrics():
    engine = create_engine("postgresql+psycopg2://hirepulse@localhost:55432/hirepulse_sql", future=True)
    report = calculate_kpis(engine, date(2026, 9, 23))
    assert list(report["Metric"]) == ["Revenue", "Active Users", "AOV", "Churn Rate", "Satisfaction"]
    assert report["Current"].notna().all()
    assert report["Prior"].notna().all()
    assert report["Change_Display"].notna().all()