SELECT
    c.customer_id,
    c.customer_name,
    c.city,
    o.order_id,
    o.order_amount,
    f.total_transactions,
    f.total_spent,
    f.days_since_last_purchase,
    f.purchase_count
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
LEFT JOIN customer_features f
    ON c.customer_id = f.customer_id
ORDER BY c.customer_id, o.order_id;
