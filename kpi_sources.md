# KPI Sources and Data Lineage

The KPI calculations use PostgreSQL 18 (`hirepulse_sql`) plus the existing
version-controlled sales dataset. Periods are calculated dynamically from the
database/current system date using first-of-month and next-month boundaries.

## Revenue KPI

- **Source:** `data/visualization_sales.csv`, because the PostgreSQL `orders`
  table contains only the earlier assignment's August/September sample while
  this validated sales dataset provides the reporting history.
- **Calculation:** Sum `order_amount` where `order_date >= current_month_start`
  and `< next_month_start`; repeat for the previous month.
- **Validation:** Recomputed from the same source with pandas and checked for
  matching current/prior values.

## Active Users KPI

- **Source:** PostgreSQL `logins(user_id, login_at)`.
- **Calculation:** Distinct `user_id` values whose `login_at` is within each
  calendar month.
- **Validation:** The result is calculated directly from the database rows by
  pandas using the same half-open date ranges.

## AOV KPI

- **Source:** `data/visualization_sales.csv`, columns `order_date` and
  `order_amount`.
- **Calculation:** Mean `order_amount` for each calendar month.
- **Validation:** pandas period mean over the same parsed dates and rows.

## Churn Rate KPI

- **Source:** PostgreSQL `orders(customer_id, order_date, order_amount,
  order_status)`.
- **Calculation:** Customers with completed positive orders in the prior month
  and no completed positive order in the following/current month, divided by
  prior-month active customers.
- **Validation:** This follows the project's validated SQL insight definition
  and is independently recomputed with pandas sets.

## Satisfaction KPI

- **Source:** `data/customer_satisfaction.csv`, created for this assignment
  because inspection found no rating/satisfaction field in PostgreSQL or the
  existing clean CSV layer.
- **Calculation:** Mean `rating` per calendar month; ratings use a 1-5 scale.
- **Validation:** Parsed source rows are aggregated by pandas for current and
  prior periods. The source and limitation are explicit so the value is not
  mistaken for a database-backed customer survey.

## Dashboard and Lineage Guarantees

- KPI values are calculated at runtime and are not hardcoded.
- Current and prior periods cross month/year boundaries correctly.
- Previous-period zero values return `0%` when both periods are zero and `N/A`
  when a nonzero current value has no denominator.
- Normal metrics mark increases positive and decreases negative; churn reverses
  that business meaning. Status colors are green `#10b981`, red `#ef4444`, and
  yellow `#f59e0b`.
- The KPI table is cross-checked by the executable calculation path and tests.