from logical_plan import build_logical_plan, print_plan
from rewrite_engine import remove_redundant_predicates


tests = {

    "Exact duplicate":
    """
    SELECT cust_id, name
    FROM customer
    WHERE acct_balance > 5000
      AND acct_balance > 5000
    """,

    "Subsumption":
    """
    SELECT cust_id, name
    FROM customer
    WHERE acct_balance > 1000
      AND acct_balance > 5000
    """,

    "Less-than subsumption":
    """
    SELECT cust_id, name
    FROM customer
    WHERE acct_balance < 9000
      AND acct_balance < 5000
    """
}


for name, sql in tests.items():

    print("=" * 70)
    print(name)
    print("=" * 70)

    plan = build_logical_plan(sql)

    print("\nBEFORE:")
    print_plan(plan)

    rewritten = remove_redundant_predicates(plan)

    print("\nAFTER:")
    print_plan(rewritten)

    print()
    

def rewrite(plan):
    """
    Apply all Phase 3 heuristic rewrite rules.

    Order:
    1. Remove redundant predicates
    2. Push selections down
    3. Push projections down
    """

    plan = remove_redundant_predicates(plan)
    plan = push_selections(plan)
    plan = push_projections(plan)

    return plan