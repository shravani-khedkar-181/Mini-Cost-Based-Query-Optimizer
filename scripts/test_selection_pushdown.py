from logical_plan import build_logical_plan, print_plan
from rewrite_engine import push_selections


def test_query(name, sql):

    print("=" * 70)
    print(name)
    print("=" * 70)

    plan = build_logical_plan(sql)

    print("\nBEFORE:")
    print_plan(plan)

    rewritten = push_selections(plan)

    print("\nAFTER:")
    print_plan(rewritten)

    print()


# ------------------------------------------------------------
# Test 1
# ------------------------------------------------------------

test_query(
    "Q5 - Customer + Orders",
    """
    SELECT c.name, o.order_id, o.total_price
    FROM customer c
    JOIN orders o
        ON c.cust_id = o.cust_id
    WHERE o.order_status = 'F'
    """
)


# ------------------------------------------------------------
# Test 2
# ------------------------------------------------------------

test_query(
    "Q7 - Customer + Orders + LineItem",
    """
    SELECT c.name, o.order_id, l.extended_price
    FROM customer c
    JOIN orders o
        ON c.cust_id = o.cust_id
    JOIN lineitem l
        ON o.order_id = l.order_id
    WHERE o.order_status = 'F'
      AND l.discount > 0.05
    """
)


# ------------------------------------------------------------
# Test 3
# ------------------------------------------------------------

test_query(
    "Q10 - Five-table query",
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
    WHERE o.order_status = 'F'
      AND l.discount > 0.05
      AND n.regionid = 1
    """
)

test_query(
    "Both-side predicate",
    """
    SELECT c.name, o.total_price
    FROM customer c
    JOIN orders o
        ON c.cust_id = o.cust_id
    WHERE c.acct_balance > o.total_price
    """
)