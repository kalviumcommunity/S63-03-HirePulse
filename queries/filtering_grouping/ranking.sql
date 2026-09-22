-- Task 5: ORDER BY Ranking
-- RANK() assigns a revenue rank to each customer.
-- ORDER BY surfaces the highest-revenue customers first.
-- LIMIT returns the top N customers.

SELECT
    customer_id,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_revenue,
    ROUND(AVG(amount), 2) AS avg_transaction,
    RANK() OVER (
        ORDER BY SUM(amount) DESC
    ) AS revenue_rank
FROM transactions
WHERE transaction_date >= '2025-01-01'
  AND amount > 0
GROUP BY customer_id
ORDER BY total_revenue DESC
LIMIT 20;
