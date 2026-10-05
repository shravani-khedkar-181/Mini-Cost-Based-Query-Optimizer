-- ============================================================
-- Phase 2 Test Queries
-- SQL subset: SELECT-FROM-WHERE-JOIN
-- ============================================================


-- ------------------------------------------------------------
-- Q1: Single-table query
-- ------------------------------------------------------------

SELECT name, acct_balance
FROM customer
WHERE acct_balance > 5000;


-- ------------------------------------------------------------
-- Q2: Single-table query with multiple predicates
-- ------------------------------------------------------------

SELECT cust_id, name
FROM customer
WHERE acct_balance > 5000
  AND market_segment = 'AUTOMOBILE';


-- ------------------------------------------------------------
-- Q3: Single-table query on orders
-- ------------------------------------------------------------

SELECT order_id, total_price
FROM orders
WHERE order_status = 'F';


-- ------------------------------------------------------------
-- Q4: Two-table join
-- ------------------------------------------------------------

SELECT c.name, o.total_price
FROM customer c
JOIN orders o
    ON c.cust_id = o.cust_id;


-- ------------------------------------------------------------
-- Q5: Two-table join with filter
-- ------------------------------------------------------------

SELECT c.name, o.order_id, o.total_price
FROM customer c
JOIN orders o
    ON c.cust_id = o.cust_id
WHERE o.order_status = 'F';


-- ------------------------------------------------------------
-- Q6: Three-table join
-- ------------------------------------------------------------

SELECT c.name, o.order_id, l.extended_price
FROM customer c
JOIN orders o
    ON c.cust_id = o.cust_id
JOIN lineitem l
    ON o.order_id = l.order_id;


-- ------------------------------------------------------------
-- Q7: Three-table join with multiple filters
-- ------------------------------------------------------------

SELECT c.name, o.order_id, l.extended_price
FROM customer c
JOIN orders o
    ON c.cust_id = o.cust_id
JOIN lineitem l
    ON o.order_id = l.order_id
WHERE o.order_status = 'F'
  AND l.discount > 0.05;


-- ------------------------------------------------------------
-- Q8: Four-table join
-- ------------------------------------------------------------

SELECT c.name, o.order_id, s.name
FROM customer c
JOIN orders o
    ON c.cust_id = o.cust_id
JOIN lineitem l
    ON o.order_id = l.order_id
JOIN supplier s
    ON l.supplierid = s.supplierid;


-- ------------------------------------------------------------
-- Q9: Five-table join
-- ------------------------------------------------------------

SELECT c.name,
       o.order_id,
       l.extended_price,
       s.name,
       n.name
FROM customer c
JOIN orders o
    ON c.cust_id = o.cust_id
JOIN lineitem l
    ON o.order_id = l.order_id
JOIN supplier s
    ON l.supplierid = s.supplierid
JOIN nation n
    ON s.nationid = n.nationid;


-- ------------------------------------------------------------
-- Q10: Five-table join with filters
-- ------------------------------------------------------------

SELECT c.name,
       o.order_id,
       l.extended_price,
       s.name,
       n.name
FROM customer c
JOIN orders o
    ON c.cust_id = o.cust_id
JOIN lineitem l
    ON o.order_id = l.order_id
JOIN supplier s
    ON l.supplierid = s.supplierid
JOIN nation n
    ON s.nationid = n.nationid
WHERE o.order_status = 'F'
  AND l.discount > 0.05
  AND n.regionid = 1;