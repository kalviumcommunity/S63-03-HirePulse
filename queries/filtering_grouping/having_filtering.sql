-- Task 3: HAVING Filtering
-- WHERE filters individual transaction rows.
-- HAVING filters customers after their transactions are aggregated.
-- The thresholds are demonstration business rules.

SELECT
    customer_id,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_revenue
FROM transactions
WHERE transaction_date >= '2025-01-01'
  AND amount > 0
GROUP BY customer_id
HAVING SUM(amount) > 1000
   AND COUNT(*) >= 1
ORDER BY total_revenue DESC;
