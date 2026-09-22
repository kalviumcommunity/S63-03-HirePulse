-- Task 4: WHERE + HAVING Combined
--
-- WHERE:
--   Removes invalid/non-positive transaction rows before aggregation.
--
-- HAVING:
--   Keeps only customer groups whose aggregated revenue
--   exceeds the business threshold.

SELECT
    customer_id,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_revenue,
    ROUND(AVG(amount), 2) AS avg_transaction
FROM transactions
WHERE transaction_date >= '2025-01-01'
  AND amount > 0
GROUP BY customer_id
HAVING SUM(amount) > 1000
ORDER BY total_revenue DESC;
