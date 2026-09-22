-- Monthly Active Users
-- A customer is active when they have at least one transaction in a month.

SELECT
    strftime('%Y-%m-01', transaction_date) AS month,
    COUNT(DISTINCT customer_id) AS active_users,
    COUNT(DISTINCT CASE
        WHEN customer_id IN (
            SELECT customer_id
            FROM customer_segments
            WHERE customer_type = 'Enterprise'
        )
        THEN customer_id
    END) AS enterprise_users,
    COUNT(DISTINCT CASE
        WHEN customer_id IN (
            SELECT customer_id
            FROM customer_segments
            WHERE customer_type = 'SMB'
        )
        THEN customer_id
    END) AS smb_users
FROM transactions
GROUP BY strftime('%Y-%m-01', transaction_date)
ORDER BY month DESC;
