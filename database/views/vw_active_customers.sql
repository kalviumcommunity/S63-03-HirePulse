-- Object: vw_active_customers
-- Purpose: expose customers with at least one completed order in the rolling
--          30-day window ending on the database server's current date.
-- Business metric: recent customer activity, order frequency, and revenue.
-- Intended users: recruiters are not consumers of this legacy customer layer;
--                 analysts and dashboard users use it for retention monitoring.
-- Grain: one row per non-deleted active customer.
-- Output columns:
--   customer_id       stable customer identifier
--   customer_name     display name
--   segment           customer segment
--   order_count_30d   distinct completed orders in the rolling window
--   revenue_30d       completed revenue in the rolling window
--   last_order_date   latest completed order date in the window
--   days_since_order  days from last order to CURRENT_DATE

DROP VIEW IF EXISTS vw_active_customers;

CREATE VIEW vw_active_customers AS
SELECT
    c.customer_id,
    c.customer_name,
    c.segment,
    COUNT(DISTINCT o.order_id) AS order_count_30d,
    COALESCE(SUM(o.order_amount), 0.00)::NUMERIC(14, 2) AS revenue_30d,
    MAX(o.order_date) AS last_order_date,
    CURRENT_DATE - MAX(o.order_date) AS days_since_order
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.customer_id
   AND o.order_date >= CURRENT_DATE - INTERVAL '30 days'
   AND o.order_status = 'completed'
WHERE c.deleted_at IS NULL
GROUP BY
    c.customer_id,
    c.customer_name,
    c.segment;