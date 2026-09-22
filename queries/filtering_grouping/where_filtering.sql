-- Task 1: WHERE Filtering
-- WHERE removes invalid rows before GROUP BY.
-- amount > 0 keeps only positive revenue transactions.
-- transaction_date >= '2025-01-01' limits the reporting period.
-- The source data does not contain transaction_status,
-- so no status filter is invented.

SELECT
    customer_id,
    SUM(amount) AS total_revenue,
    COUNT(*) AS transaction_count
FROM transactions
WHERE transaction_date >= '2025-01-01'
  AND amount > 0
GROUP BY customer_id
ORDER BY total_revenue DESC;
