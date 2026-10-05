import sqlglot

sql = """
SELECT c.name, o.total_price
FROM customer c
JOIN orders o
    ON c.cust_id = o.cust_id
WHERE o.order_status = 'F'
"""

tree = sqlglot.parse_one(sql)

print("SQL:")
print(sql)

print("\nAST:")
print(tree)

print("\nAST representation:")
print(repr(tree))