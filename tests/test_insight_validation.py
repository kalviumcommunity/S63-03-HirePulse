"""Integration tests for SQL-Based Insight Validation."""

from validation_script import validate_metrics


def test_all_insight_metrics_match():
    from sqlalchemy import create_engine

    engine = create_engine(
        "postgresql+psycopg2://hirepulse@localhost:55432/hirepulse_sql",
        future=True,
    )
    report = validate_metrics(engine)

    assert list(report["Metric"]) == [
        "Active Users (30-day)",
        "Average Order Value",
        "Monthly Customer Churn",
    ]
    assert report["Status"].eq("PASS").all()
    assert (report["Difference"] == 0).all()