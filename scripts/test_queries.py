TEST_QUERIES = {

    "Q1_single_table_filter": """
        SELECT name, acct_balance
        FROM customer
        WHERE acct_balance > 5000
    """,

    "Q2_single_table_multiple_filters": """
        SELECT cust_id, name
        FROM customer
        WHERE acct_balance > 5000
          AND market_segment = 'AUTOMOBILE'
    """,

    "Q3_orders_filter": """
        SELECT order_id, total_price
        FROM orders
        WHERE order_status = 'F'
    """,

    "Q4_customer_orders": """
        SELECT c.name, o.total_price
        FROM customer c
        JOIN orders o
            ON c.cust_id = o.cust_id
    """,

    "Q5_customer_orders_filter": """
        SELECT c.name, o.order_id, o.total_price
        FROM customer c
        JOIN orders o
            ON c.cust_id = o.cust_id
        WHERE o.order_status = 'F'
    """,

    "Q6_customer_orders_lineitem": """
        SELECT c.name, o.order_id, l.extended_price
        FROM customer c
        JOIN orders o
            ON c.cust_id = o.cust_id
        JOIN lineitem l
            ON o.order_id = l.order_id
    """,

    "Q7_three_table_filters": """
        SELECT c.name, o.order_id, l.extended_price
        FROM customer c
        JOIN orders o
            ON c.cust_id = o.cust_id
        JOIN lineitem l
            ON o.order_id = l.order_id
        WHERE o.order_status = 'F'
          AND l.discount > 0.05
    """,

    "Q8_four_table_join": """
        SELECT c.name, o.order_id, s.name
        FROM customer c
        JOIN orders o
            ON c.cust_id = o.cust_id
        JOIN lineitem l
            ON o.order_id = l.order_id
        JOIN supplier s
            ON l.supplierid = s.supplierid
    """,

    "Q9_five_table_join": """
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
    """,

    "Q10_five_table_filters": """
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
          AND n.regionid = 1
    """,
    
    "Q11_redundant_predicate": """
        SELECT cust_id, name
        FROM customer
        WHERE acct_balance > 1000
          AND acct_balance > 5000
    """,
}