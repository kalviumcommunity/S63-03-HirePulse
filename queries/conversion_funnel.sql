-- Customer Signup to Transaction Conversion
-- Conversion requires a matching customer_id between customers
-- and transactions.

SELECT
    c.signup_date,
    COUNT(DISTINCT c.customer_id) AS signups,
    COUNT(DISTINCT t.customer_id) AS converted_customers,
    ROUND(
        100.0 * COUNT(DISTINCT t.customer_id)
        / NULLIF(COUNT(DISTINCT c.customer_id), 0),
        1
    ) AS conversion_pct
FROM customers c
LEFT JOIN transactions t
    ON CAST(c.customer_id AS TEXT) = CAST(t.customer_id AS TEXT)
GROUP BY c.signup_date
ORDER BY c.signup_date DESC;
