-- Object: vw_revenue_by_region
-- Purpose: summarize completed order performance by customer region and country.
-- Business question: which geographic markets generate the most completed revenue?
-- Intended users: business analysts and leadership comparing market performance.
-- Grain: one row per region/country pair with at least one completed order.
-- Output columns:
--   region              geographic sales region
--   country             customer country
--   customer_count     distinct non-deleted customers ordering in the dataset
--   order_count        completed orders
--   total_revenue      completed order revenue
--   average_order_value average completed order amount

DROP VIEW IF EXISTS vw_revenue_by_region;

CREATE VIEW vw_revenue_by_region AS
SELECT
    c.region,
    c.country,
    COUNT(DISTINCT c.customer_id) AS customer_count,
    COUNT(o.order_id) AS order_count,
    SUM(o.order_amount)::NUMERIC(14, 2) AS total_revenue,
    AVG(o.order_amount)::NUMERIC(14, 2) AS average_order_value
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.customer_id
WHERE c.deleted_at IS NULL
  AND o.order_status = 'completed'
  AND o.order_date <= CURRENT_DATE
GROUP BY
    c.region,
    c.country;