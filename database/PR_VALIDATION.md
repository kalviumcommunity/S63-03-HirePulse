# SQL Layer Validation

This branch contains the complete SQL Views & Aggregation Layer implementation.

## Included Objects

- `vw_active_customers`
- `vw_revenue_by_region`
- `agg_daily_metrics`

## Verified Checks

- PostgreSQL 18 database connection succeeds on the configured local database.
- Both SQL views are queryable.
- The daily aggregate table contains populated `updated_at` values.
- The SQLAlchemy and pandas demonstration runs successfully.
- The integration test suite passes with four tests.

## Reproduce

```bash
.venv-1/Scripts/python.exe scripts/setup_sql_database.py
.venv-1/Scripts/python.exe assignment-33-python.py
.venv-1/Scripts/python.exe -m pytest -q tests/test_sql_data_layer.py
```