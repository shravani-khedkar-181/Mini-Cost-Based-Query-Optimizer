import json
from pathlib import Path

import sqlglot
from sqlglot import exp

try:
    from logical_plan import Scan, Selection, Projection, Join
except ModuleNotFoundError:
    from scripts.logical_plan import Scan, Selection, Projection, Join

# Load Phase 1 statistics
BASE_DIR = Path(__file__).resolve().parent.parent
STATS_FILE = BASE_DIR / "stats" / "baseline_stats.json"

with open(STATS_FILE, "r") as f:
    STATS = json.load(f)


def get_row_count(table):
    return STATS[table]["row_count"]


def get_distinct_count(table, column):
    return STATS[table]["columns"][column]["distinct"]

# SQL aliases used in our test queries
TABLE_ALIASES = {
    "c": "customer",
    "o": "orders",
    "l": "lineitem",
    "s": "supplier",
    "n": "nation",
}


def resolve_table_name(table_or_alias):
    """
    Convert a SQL table alias into the actual table name.
    If it is already a real table name, return it unchanged.
    """
    return TABLE_ALIASES.get(table_or_alias, table_or_alias)


def estimate_selectivity(predicate, left_table=None, right_table=None):
    """
    Estimate predicate selectivity using simple textbook formulas.

    Equality:
        selectivity = 1 / distinct_count

    Range:
        selectivity = 1 / 3

    AND:
        Multiply the selectivities of the individual predicates.
    """

    # Combined predicates: A AND B
    if isinstance(predicate, exp.And):
        left_selectivity = estimate_selectivity(
            predicate.this, left_table, right_table
        )
        right_selectivity = estimate_selectivity(
            predicate.expression, left_table, right_table
        )
        return left_selectivity * right_selectivity

    # Join equality: a.col = b.col
    if isinstance(predicate, exp.EQ):
        left = predicate.this
        right = predicate.expression

        if isinstance(left, exp.Column) and isinstance(right, exp.Column):
            left_table_name = resolve_table_name(left.table)
            right_table_name = resolve_table_name(right.table)

            if left_table_name and right_table_name:
                left_distinct = get_distinct_count(
                    left_table_name, left.name
                )
                right_distinct = get_distinct_count(
                    right_table_name, right.name
                )

                return 1 / max(left_distinct, right_distinct)

        # Normal equality: col = value
        if isinstance(left, exp.Column):
            table = resolve_table_name(left_table)
            column = left.name

            if table:
                return 1 / get_distinct_count(table, column)

    # Range predicates
    if isinstance(predicate, (exp.GT, exp.GTE, exp.LT, exp.LTE)):
        return 1 / 3

    # Fallback for unsupported predicates
    return 1 / 3

def estimate_rows(node):
    """
    Recursively estimate the number of rows produced by a logical-plan node.
    The result is stored in node.estimated_rows.
    """

    # Scan
    if isinstance(node, Scan):
        table = resolve_table_name(node.table)
        node.estimated_rows = get_row_count(table)
        return node.estimated_rows

    # Selection
    if isinstance(node, Selection):
        child_rows = estimate_rows(node.child)

        table = None

        # Find the table referenced by the predicate.
        if isinstance(node.predicate, exp.Expression):
            columns = list(node.predicate.find_all(exp.Column))

            if columns:
                col = columns[0]
                
                if col.table:
                    table = resolve_table_name(col.table)
                else:
                    table = get_single_table_name(node.child)

        selectivity = estimate_selectivity(
            node.predicate,
            table
        )

        node.estimated_rows = child_rows * selectivity
        return node.estimated_rows

    # Projection
    if isinstance(node, Projection):
        node.estimated_rows = estimate_rows(node.child)
        return node.estimated_rows

    # Join
    if isinstance(node, Join):
        left_rows = estimate_rows(node.left)
        right_rows = estimate_rows(node.right)

        columns = list(node.condition.find_all(exp.Column))

        if len(columns) >= 2:
            left_table = resolve_table_name(columns[0].table)
            right_table = resolve_table_name(columns[1].table)

            selectivity = estimate_selectivity(
                node.condition,
                left_table,
                right_table
            )
        else:
            selectivity = 1 / 3

        node.estimated_rows = (
            left_rows * right_rows * selectivity
        )

        return node.estimated_rows

    raise TypeError(
        f"Unsupported node type: {type(node).__name__}"
    )
    
def estimate_cost(node):
    """
    Estimate the cost of a logical plan.

    Cost model:
    - Scan: rows / 100
    - Selection: cost of child
    - Projection: cost of child
    - Join: left cost + right cost + output rows
    """

    # Scan
    if isinstance(node, Scan):
        rows = estimate_rows(node)
        return rows / 100

    # Selection
    if isinstance(node, Selection):
        return estimate_cost(node.child)

    # Projection
    if isinstance(node, Projection):
        return estimate_cost(node.child)

    # Join
    if isinstance(node, Join):
        left_cost = estimate_cost(node.left)
        right_cost = estimate_cost(node.right)
        output_rows = estimate_rows(node)

        return left_cost + right_cost + output_rows

    raise TypeError(f"Unknown node type: {type(node)}")

def get_single_table_name(node):
    """Resolve the table for an unqualified column in a single-table subtree."""
    if isinstance(node, Scan):
        return resolve_table_name(node.table)

    if isinstance(node, Selection):
        return get_single_table_name(node.child)

    if isinstance(node, Projection):
        return get_single_table_name(node.child)

    raise ValueError(
        "get_single_table_name called on a multi-table subtree"
    )