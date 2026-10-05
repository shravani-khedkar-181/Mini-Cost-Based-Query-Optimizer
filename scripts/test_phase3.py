from logical_plan import build_logical_plan, print_plan
from rewrite_engine import rewrite
from test_queries import TEST_QUERIES


for name, sql in TEST_QUERIES.items():

    print("=" * 70)
    print(name)
    print("=" * 70)

    print("\nSQL:")
    print(sql.strip())

    # --------------------------------------------------------
    # BEFORE
    # --------------------------------------------------------

    before = build_logical_plan(sql)

    print("\nBEFORE:")
    print_plan(before)

    # --------------------------------------------------------
    # AFTER
    # --------------------------------------------------------

    after = rewrite(before)

    print("\nAFTER:")
    print_plan(after)

    print()