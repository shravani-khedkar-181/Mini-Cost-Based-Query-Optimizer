from logical_plan import build_logical_plan, print_plan
from test_queries import TEST_QUERIES


def main():

    print("=" * 70)
    print("PHASE 2 — SQL PARSER & LOGICAL PLAN TEST")
    print("=" * 70)

    for name, sql in TEST_QUERIES.items():

        print()
        print("-" * 70)
        print(name)
        print("-" * 70)

        print("SQL:")
        print(sql.strip())

        print()
        print("Logical Plan:")

        try:

            plan = build_logical_plan(sql)

            print_plan(plan)

            print()
            print("STATUS: PASS")

        except Exception as error:

            print()
            print("STATUS: FAIL")
            print(f"ERROR: {error}")


if __name__ == "__main__":
    main()