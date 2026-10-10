from join_order_search import (
    extract_join_graph,
    build_logical_plan,
    dynamic_programming_join_search,
)


def test_two_table_join():
    sql = (
        "SELECT c.name, o.total_price "
        "FROM customer c "
        "JOIN orders o ON c.cust_id = o.cust_id"
    )

    plan = build_logical_plan(sql)
    tables, conditions = extract_join_graph(plan)
    best, dp = dynamic_programming_join_search(tables, conditions)

    assert len(tables) == 2
    assert len(conditions) == 1
    assert best["cost"] > 0
    assert best["rows"] > 0
    assert len(dp) == 3

    print("PASS: Two-table join")
    print("  Best cost:", best["cost"])
    print("  Estimated rows:", best["rows"])


def test_three_table_join():
    sql = (
        "SELECT c.name, o.order_id, l.extended_price "
        "FROM customer c "
        "JOIN orders o ON c.cust_id = o.cust_id "
        "JOIN lineitem l ON o.order_id = l.order_id"
    )

    plan = build_logical_plan(sql)
    tables, conditions = extract_join_graph(plan)
    best, dp = dynamic_programming_join_search(tables, conditions)

    assert len(tables) == 3
    assert len(conditions) == 2
    assert best["cost"] > 0
    assert best["rows"] > 0
    assert len(dp) == 6

    print("PASS: Three-table join")
    print("  Best cost:", best["cost"])
    print("  Estimated rows:", best["rows"])
    print("  DP subset count:", len(dp))


def test_dp_selects_lower_cost_join_order():
    from sqlglot import parse_one, exp
    from logical_plan import Scan, Join
    from cost_model import estimate_cost

    c = Scan(table="customer", alias="c")
    o = Scan(table="orders", alias="o")
    l = Scan(table="lineitem", alias="l")

    customer_orders = Join(
        condition=parse_one("c.cust_id = o.cust_id", into=exp.Condition),
        left=c,
        right=o,
    )

    orders_lineitem = Join(
        condition=parse_one("o.order_id = l.order_id", into=exp.Condition),
        left=o,
        right=l,
    )

    order1 = Join(
        condition=parse_one("o.order_id = l.order_id", into=exp.Condition),
        left=customer_orders,
        right=l,
    )

    order2 = Join(
        condition=parse_one("c.cust_id = o.cust_id", into=exp.Condition),
        left=c,
        right=orders_lineitem,
    )

    cost1 = estimate_cost(order1)
    cost2 = estimate_cost(order2)

    assert cost1 < cost2, (
        f"Expected Order 1 to be cheaper, got {cost1} vs {cost2}"
    )

    print("PASS: Lower-cost join order verified")
    print("  Order 1 cost:", cost1)
    print("  Order 2 cost:", cost2)


def test_multiple_join_predicates():
    from sqlglot import parse_one, exp
    from logical_plan import Scan, Join
    from cost_model import estimate_rows

    left = Scan(table="customer", alias="c")
    right = Scan(table="orders", alias="o")

    condition = parse_one(
        "c.cust_id = o.cust_id AND c.cust_id > 100",
        into=exp.Condition,
    )

    plan = Join(
        condition=condition,
        left=left,
        right=right,
    )

    rows = estimate_rows(plan)

    assert rows > 0, f"Expected positive row estimate, got {rows}"

    # Both equality predicates should contribute to selectivity.
    single_condition = Join(
        condition=parse_one(
            "c.cust_id = o.cust_id",
            into=exp.Condition,
        ),
        left=Scan(table="customer", alias="c"),
        right=Scan(table="orders", alias="o"),
    )

    single_rows = estimate_rows(single_condition)

    assert rows < single_rows, (
        f"Expected combined predicates to reduce rows: "
        f"{rows} should be less than {single_rows}"
    )

    print("PASS: Multiple join predicates")
    print("  Single-predicate rows:", single_rows)
    print("  Two-predicate rows:", rows)


def test_disconnected_join_graph():
    from join_order_search import dynamic_programming_join_search
    from logical_plan import Scan
    from sqlglot import parse_one, exp

    tables = ["c", "o", "s"]

    # Only customer and orders are connected.
    join_conditions = [
        parse_one(
            "c.cust_id = o.cust_id",
            into=exp.Condition,
        )
    ]

    try:
        dynamic_programming_join_search(tables, join_conditions)
    except ValueError:
        print("PASS: Disconnected join graph rejected")
    else:
        raise AssertionError(
            "Expected ValueError for a disconnected join graph"
        )


def test_join_condition_requires_all_tables():
    from sqlglot import parse_one, exp
    from join_order_search import is_join_condition_between

    condition = parse_one(
        "c.cust_id = o.cust_id AND o.order_id = l.order_id",
        into=exp.Condition,
    )

    # This condition references c, o, and l.
    # It must not be accepted when only c and o are available.
    result = is_join_condition_between(
        condition,
        {"c"},
        {"o"},
    )

    assert result is False, (
        "A condition referencing an unavailable table "
        "must not be treated as a valid join condition."
    )

    print("PASS: Join condition requires all referenced tables")


if __name__ == "__main__":
    test_two_table_join()
    test_three_table_join()
    test_dp_selects_lower_cost_join_order()
    test_multiple_join_predicates()
    test_disconnected_join_graph()
    test_join_condition_requires_all_tables()
    print("\nAll Phase 5 tests passed.")

