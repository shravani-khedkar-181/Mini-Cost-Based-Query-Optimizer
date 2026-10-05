from dataclasses import dataclass
from typing import Optional, List

import sqlglot
from sqlglot import exp


# ============================================================
# Logical Plan Node Classes
# ============================================================

@dataclass
class Scan:
    table: str
    alias: Optional[str] = None


@dataclass
class Selection:
    predicate: str
    child: object


@dataclass
class Projection:
    columns: List[str]
    child: object


@dataclass
class Join:
    condition: str
    left: object
    right: object


# ============================================================
# Helper Functions
# ============================================================

def expression_to_string(expression):
    """Convert a SQLGlot expression back into readable SQL."""
    return expression.sql()


def get_table_scan(table_expression):
    """Create a Scan node from a SQLGlot Table expression."""

    table_name = table_expression.name

    alias = None
    if table_expression.alias:
        alias = table_expression.alias

    return Scan(
        table=table_name,
        alias=alias
    )


# ============================================================
# WHERE Predicate Handling
# ============================================================

def split_and_predicates(expression):
    """
    Split:
        A AND B AND C

    into:
        [A, B, C]

    This is important for Phase 3 because individual
    Selection nodes can later be pushed down independently.
    """

    if isinstance(expression, exp.And):
        return (
            split_and_predicates(expression.this)
            + split_and_predicates(expression.expression)
        )

    return [expression]


# ============================================================
# Logical Plan Builder
# ============================================================

def build_logical_plan(sql: str):
    """
    Convert a SQL SELECT-FROM-WHERE-JOIN query
    into our relational algebra tree.
    """

    tree = sqlglot.parse_one(sql)

    if not isinstance(tree, exp.Select):
        raise ValueError("Only SELECT queries are supported.")

    # --------------------------------------------------------
    # 1. FROM
    # --------------------------------------------------------

    from_clause = tree.args.get("from_")

    if from_clause is None:
        raise ValueError("Query must contain a FROM clause.")

    base_table = from_clause.this

    if not isinstance(base_table, exp.Table):
        raise ValueError("FROM must contain a table.")

    plan = get_table_scan(base_table)

    # --------------------------------------------------------
    # 2. JOIN
    # --------------------------------------------------------

    for join_expression in tree.args.get("joins", []):

        right_table = join_expression.this

        if not isinstance(right_table, exp.Table):
            raise ValueError(
                "Only joins directly involving tables are supported."
            )

        right_plan = get_table_scan(right_table)

        join_condition = join_expression.args.get("on")

        if join_condition is None:
            raise ValueError(
                "JOIN must contain an ON condition."
            )

        plan = Join(
            condition=expression_to_string(join_condition),
            left=plan,
            right=right_plan
        )

    # --------------------------------------------------------
    # 3. WHERE
    # --------------------------------------------------------

    where_clause = tree.args.get("where")

    if where_clause is not None:

        predicates = split_and_predicates(
            where_clause.this
        )

        # Build Selection nodes from bottom to top.
        for predicate in predicates:
            plan = Selection(
                predicate=expression_to_string(predicate),
                child=plan
            )

    # --------------------------------------------------------
    # 4. SELECT / PROJECTION
    # --------------------------------------------------------

    columns = []

    for expression in tree.expressions:

        columns.append(
            expression_to_string(expression)
        )

    plan = Projection(
        columns=columns,
        child=plan
    )

    return plan


# ============================================================
# Plan Printer
# ============================================================

def print_plan(node, indent=0):

    prefix = "  " * indent

    if isinstance(node, Projection):

        print(
            f"{prefix}Projection[{', '.join(node.columns)}]"
        )

        print_plan(
            node.child,
            indent + 1
        )

    elif isinstance(node, Selection):

        print(
            f"{prefix}Selection[{node.predicate}]"
        )

        print_plan(
            node.child,
            indent + 1
        )

    elif isinstance(node, Join):

        print(
            f"{prefix}Join[{node.condition}]"
        )

        print_plan(
            node.left,
            indent + 1
        )

        print_plan(
            node.right,
            indent + 1
        )

    elif isinstance(node, Scan):

        if node.alias:

            print(
                f"{prefix}Scan[{node.table} AS {node.alias}]"
            )

        else:

            print(
                f"{prefix}Scan[{node.table}]"
            )

    else:

        raise TypeError(
            f"Unknown plan node: {type(node)}"
        )


# ============================================================
# Simple Test
# ============================================================

if __name__ == "__main__":

#     sql = """
# SELECT c.name, o.order_id, l.extended_price
# FROM customer c
# JOIN orders o
#     ON c.cust_id = o.cust_id
# JOIN lineitem l
#     ON o.order_id = l.order_id
# WHERE o.order_status = 'F'
# """

    plan = build_logical_plan(sql)

    print("Logical Plan:")
    print()

    print_plan(plan)
    
