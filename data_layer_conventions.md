# SQL Data-Layer Conventions

This assignment uses the isolated PostgreSQL database `hirepulse_sql` on the
local PostgreSQL cluster at port `55432`. The source schema is documented in
`database/schema.sql`.

## Views

Prefix:

`vw_`

Pattern:

`vw_[business_entity]_[metric]`

Examples:

- `vw_active_customers`
- `vw_revenue_by_region`

Views are appropriate for reusable, current calculations that should remain
close to source data and do not need their own stored refresh lifecycle.

## Aggregated Tables

Prefix:

`agg_`

Pattern:

`agg_[grain]_[subject]`

Examples:

- `agg_daily_metrics`
- `agg_daily_revenue`

Physical aggregate tables are appropriate for repeated dashboard reads where a
precomputed grain improves performance. Aggregated tables should include:

- an explicit time/date grain;
- `updated_at` to show refresh timing; and
- `row_count` where it explains the contributing source population.

## Objects Created

- `vw_active_customers`: one row per non-deleted customer with completed order
  activity in the rolling 30-day window.
- `vw_revenue_by_region`: completed revenue and order metrics by region/country.
- `agg_daily_metrics`: daily completed revenue at date/metric grain.

The convention keeps object purpose visible in names, makes related objects
easy to discover, and reduces accidental collisions between source tables,
current views, and persisted aggregates.