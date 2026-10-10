from logical_plan import build_logical_plan
from rewrite_engine import rewrite
from join_order_search import extract_join_graph, dynamic_programming_join_search
from logical_plan import print_plan

queries = {
    "Q7": """
        SELECT c.name, o.order_id, l.extended_price
        FROM customer c
        JOIN orders o ON c.cust_id = o.cust_id
        JOIN lineitem l ON o.order_id = l.order_id
        WHERE o.order_status = 'F'
          AND l.discount > 0.05
    """,
    "Q10": """
        SELECT c.name, o.order_id, l.extended_price, s.name, n.name
        FROM customer c
        JOIN orders o ON c.cust_id = o.cust_id
        JOIN lineitem l ON o.order_id = l.order_id
        JOIN supplier s ON l.supplierid = s.supplierid
        JOIN nation n ON s.nationid = n.nationid
        WHERE o.order_status = 'F'
          AND l.discount > 0.05
          AND n.regionid = 1
    """,
}

for name, sql in queries.items():
    plan = rewrite(build_logical_plan(sql))
    base_plans, join_conditions = extract_join_graph(plan)

    best, dp = dynamic_programming_join_search(
        base_plans, join_conditions
    )

    print(f"\n{name}")
    print("Aliases:", list(base_plans.keys()))
    print("Base-plan estimated rows:", {
        alias: round(dp[frozenset([alias])]["rows"], 2)
        for alias in base_plans
    })
    print("Full-plan estimated rows:", round(best["rows"], 2))
    print("Full-plan estimated cost:", round(best["cost"], 2))
    print("\nChosen DP join tree:")
    print_plan(best["plan"])
