from logical_plan import build_logical_plan, print_plan
from rewrite_engine import push_projections


def test_query(name, sql):

    print("=" * 70)
    print(name)
    print("=" * 70)

    plan = build_logical_plan(sql)

    print("\nBEFORE:")
    print_plan(plan)

    rewritten = push_projections(plan)

    print("\nAFTER:")
    print_plan(rewritten)

    print()


test_query(
    "Q6 - Customer + Orders + LineItem",
    """
    SELECT c.name, o.order_id, l.extended_price
    FROM customer c
    JOIN orders o
        ON c.cust_id = o.cust_id
    JOIN lineitem l
        ON o.order_id = l.order_id
    """
)


test_query(
    "Q8 - Four-table join",
    """
    SELECT c.name, o.order_id, s.name
    FROM customer c
    JOIN orders o
        ON c.cust_id = o.cust_id
    JOIN lineitem l
        ON o.order_id = l.order_id
    JOIN supplier s
        ON l.supplierid = s.supplierid
    """
)


test_query(
    "Q9 - Five-table join",
    """
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
    """
)