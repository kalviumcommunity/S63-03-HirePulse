-- INNER JOIN
SELECT
    c.customer_id,
    o.order_id,
    o.order_amount
FROM customers c
INNER JOIN orders o
    ON c.customer_id = o.customer_id
ORDER BY c.customer_id, o.order_id;

-- LEFT JOIN
SELECT
    c.customer_id,
    o.order_id,
    o.order_amount
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
ORDER BY c.customer_id, o.order_id;

-- FULL OUTER JOIN emulation for SQLite
SELECT
    c.customer_id,
    o.order_id,
    o.order_amount
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id

UNION ALL

SELECT
    c.customer_id,
    o.order_id,
    o.order_amount
FROM orders o
LEFT JOIN customers c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
ORDER BY customer_id, order_id;
