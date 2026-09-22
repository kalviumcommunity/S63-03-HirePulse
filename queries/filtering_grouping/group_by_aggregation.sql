-- Task 2: GROUP BY and Aggregation
-- GROUP BY changes the aggregation unit to one row per month.
-- WHERE filters transaction rows before aggregation.

SELECT
    strftime('%Y-%m-01', transaction_date) AS month,
    COUNT(DISTINCT customer_id) AS unique_customers,
    COUNT(*) AS transaction_count,
    SUM(amount) AS monthly_revenue,
    ROUND(AVG(amount), 2) AS avg_transaction
FROM transactions
WHERE transaction_date >= '2025-01-01'
  AND amount > 0
GROUP BY strftime('%Y-%m-01', transaction_date)
ORDER BY month DESC;
