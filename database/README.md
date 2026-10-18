# SQL Assignment Database

## Engine

This assignment uses PostgreSQL 18 in an isolated local cluster:

- Host: `localhost`
- Port: `55432`
- Database: `hirepulse_sql`
- User: `hirepulse`
- Connection URL: `postgresql+psycopg2://hirepulse@localhost:55432/hirepulse_sql`

The repository's pre-existing SQLite databases were inspected first. They contain
separate coursework schemas and do not contain a coherent customer/order model
for this assignment. The PostgreSQL schema is therefore defined in
`database/schema.sql` and seeded with realistic, deterministic data.

## Source Schema

### `customers`

One row per customer. Includes the customer identifier, display name, segment,
region, country, signup date, and optional soft-delete timestamp.

### `orders`

One row per order. Includes the order identifier, customer foreign key, order
date, amount, and order status. Only `completed` orders contribute to the
assignment metrics.

## Setup and Refresh

The local cluster can be initialized and refreshed with the reusable setup script:

```bash
python scripts/setup_sql_database.py
```

The script starts the isolated cluster when necessary, creates the database when
necessary, and applies the schema, views, and aggregate table. To recreate only
the database objects after the server is available, run:

```bash
psql -h localhost -p 55432 -U hirepulse -d hirepulse_sql -f database/schema.sql
psql -h localhost -p 55432 -U hirepulse -d hirepulse_sql -f database/views/vw_active_customers.sql
psql -h localhost -p 55432 -U hirepulse -d hirepulse_sql -f database/views/vw_revenue_by_region.sql
psql -h localhost -p 55432 -U hirepulse -d hirepulse_sql -f database/aggregations/agg_daily_metrics.sql
```

The Python demonstration uses this same URL by default and accepts
`DATABASE_URL` as an environment-variable override.

## SQL-Based Insight Validation

The schema also includes `logins`, which links `user_id` to
`customers.customer_id`. The validation assignment uses:

- `logins.login_at` for 30-day active users;
- `orders.order_amount` for average order value; and
- completed positive orders in the previous/current calendar months for churn.