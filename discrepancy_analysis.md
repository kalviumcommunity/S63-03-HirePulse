# SQL-Based Insight Validation

## Database and Definitions

Validation was executed against PostgreSQL 18.1 in the local `hirepulse_sql`
database. The existing `customers` and `orders` tables were reused. A linked
`logins` table was added because no suitable login table existed.

The implemented definitions are:

- **Active Users (30-day):** distinct `logins.user_id` values with a
  `login_at` timestamp from database midnight 30 days before `CURRENT_DATE`
  through the end of the current database date.
- **Average Order Value:** `AVG(orders.order_amount)` across all order rows,
  matching the assignment definition exactly.
- **Monthly Customer Churn:** customers with completed positive orders in the
  previous calendar month and no completed positive order in the current
  calendar month.

## Verified Comparison

The validation script was executed on 2026-09-23 and generated
`validation_report.csv`:

| Metric | SQL | Python | Difference | Percent Difference | Tolerance | Status |
|---|---:|---:|---:|---:|---:|---|
| Active Users (30-day) | 9 | 9 | 0 | 0% | 0% | PASS |
| Average Order Value | 1005.5535714285714 | 1005.5535714285714 | 0 | 0% | 0.1% | PASS |
| Monthly Customer Churn | 5 | 5 | 0 | 0% | 0% | PASS |

The raw-data investigation found 11 customers with qualifying August 2026
spend. Six had qualifying September activity and five did not: `C003`, `C006`,
`C009`, `C012`, and `C014`. The database date boundaries were verified as
August 1, 2026 through September 1, 2026 for the previous month and September
1, 2026 through October 1, 2026 for the current month.

## Why the Calculations Match

- Both implementations use the database's `CURRENT_DATE` as the date anchor.
- SQL uses PostgreSQL `date_trunc` and half-open month ranges, so January and
  year transitions do not depend on extracting a month number alone.
- Login timestamps are normalized to UTC in pandas and compared to the same
  midnight-to-midnight 30-day window used by SQL.
- Both churn calculations filter to completed orders with positive amounts,
  group by customer, and test current-month membership.
- PostgreSQL numeric values are converted to pandas numeric values without
  early rounding. The AOV tolerance is therefore applied to the full result.
- Empty numeric inputs are handled as zero in both validation paths, and
  percentage difference handles a zero SQL baseline without division errors.
- The seed data contains no null amounts, dates, or identifiers, and the SQL
  and pandas paths use the same source rows.

No discrepancy was discovered, so no corrective calculation change was needed.

## Why Manual Investigation Is Necessary

An automated tolerance detects divergence, not correctness. SQL and Python can
both implement the same incorrect business rule and still match exactly. Small
or creeping drift can also remain below a tolerance threshold while becoming
material over time. Manual investigation of raw records, date boundaries,
joins, null handling, and duplicates identifies the actual source of a problem.

Automatically changing one calculation based only on a threshold could silently
make the metric worse, especially when the other calculation is the incorrect
one. Understanding the root cause allows the correction to be made in the
right layer and prevents the same problem from recurring.