-- Revenue by Customer Segment
-- Revenue is sourced from the customer segment dataset.

SELECT
    customer_type,
    product,
    COUNT(*) AS customer_count,
    SUM(revenue) AS total_revenue,
    ROUND(AVG(revenue), 2) AS avg_customer_revenue,
    ROUND(
        SUM(revenue) * 1.0 / COUNT(*),
        2
    ) AS revenue_per_customer
FROM customer_segments
GROUP BY
    customer_type,
    product
ORDER BY
    total_revenue DESC;
