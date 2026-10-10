import itertools
from sqlglot import exp
try:
    from cost_model import resolve_table_name
except ModuleNotFoundError:
    from scripts.cost_model import resolve_table_name

try:
    from logical_plan import (
        Scan,
        Selection,
        Projection,
        Join,
        build_logical_plan,
    )
except ModuleNotFoundError:
    from scripts.logical_plan import (
        Scan,
        Selection,
        Projection,
        Join,
        build_logical_plan,
    )

try:
    from rewrite_engine import rewrite
except ModuleNotFoundError:
    from scripts.rewrite_engine import rewrite

try:
    from cost_model import estimate_rows, estimate_cost
except ModuleNotFoundError:
    from scripts.cost_model import estimate_rows, estimate_cost


def get_single_table_alias(node):
    """Return the alias of a single-table subtree, if applicable."""
    if isinstance(node, Scan):
        return node.alias or node.table

    if isinstance(node, Selection):
        return get_single_table_alias(node.child)

    if isinstance(node, Projection):
        return get_single_table_alias(node.child)

    return None


def extract_join_graph(plan):
    """
    Extract alias-keyed single-table plans and join conditions.

    Preserve Selection and Projection wrappers so the DP search
    starts with Phase 3's filtered and narrowed subplans.
    """
    base_plans = {}
    join_conditions = []

    def visit(node):
        if isinstance(node, Scan):
            alias = node.alias or node.table
            base_plans.setdefault(alias, node)

        elif isinstance(node, (Selection, Projection)):
            visit(node.child)

            alias = get_single_table_alias(node.child)
            if alias is not None:
                base_plans[alias] = node

        elif isinstance(node, Join):
            join_conditions.append(node.condition)
            visit(node.left)
            visit(node.right)

    visit(plan)

    return base_plans, join_conditions


def generate_join_orders(tables):
    """
    Generate possible join orders for the given tables.
    Each order is a tuple containing table names.
    """
    if not tables:
        return []

    return list(itertools.permutations(tables))

def get_join_tables(condition):
    """
    Return the table aliases referenced by a join condition.
    Example: c.cust_id = o.cust_id returns {'c', 'o'}.
    """
    aliases = set()

    for column in condition.find_all(exp.Column):
        if column.table:
            aliases.add(column.table)

    return aliases



def is_join_condition_between(condition, left_tables, right_tables):
    """
    Return True only if every referenced table belongs to one of
    the two input plans, and the condition connects both plans.
    """
    aliases = get_join_tables(condition)

    # The condition must reference tables from both sides.
    if not aliases.intersection(left_tables):
        return False

    if not aliases.intersection(right_tables):
        return False

    # Reject conditions that reference tables unavailable
    # in the two input plans.
    available_tables = left_tables | right_tables

    if not aliases.issubset(available_tables):
        return False

    return True

    
def get_plan_aliases(plan):
    """
    Return the SQL aliases available in a plan.
    If a scan has no alias, use its table name.
    """
    aliases = set()

    def visit(node):
        if isinstance(node, Scan):
            aliases.add(node.alias or node.table)

        elif isinstance(node, Selection):
            visit(node.child)

        elif isinstance(node, Projection):
            visit(node.child)

        elif isinstance(node, Join):
            visit(node.left)
            visit(node.right)

    visit(plan)
    return aliases


def find_join_condition(join_conditions, left_plan, right_plan):
    """
    Combine all join conditions connecting the two plans.
    Return None if no connecting condition exists.
    """
    left_aliases = get_plan_aliases(left_plan)
    right_aliases = get_plan_aliases(right_plan)

    matching_conditions = []

    for condition in join_conditions:
        if is_join_condition_between(
            condition,
            left_aliases,
            right_aliases
        ):
            matching_conditions.append(condition)

    if not matching_conditions:
        return None

    combined_condition = matching_conditions[0].copy()

    for condition in matching_conditions[1:]:
        combined_condition = exp.and_(
            combined_condition,
            condition.copy()
        )

    return combined_condition




def initialize_dp_table(base_plans, join_conditions=None):
    """Initialize DP entries from preserved plans or legacy table names."""
    dp = {}

    if isinstance(base_plans, dict):
        for alias, plan in base_plans.items():
            dp[frozenset([alias])] = {
                "plan": plan,
                "cost": estimate_cost(plan),
                "rows": estimate_rows(plan),
            }
        return dp

    # Legacy path used by older tests.
    join_conditions = join_conditions or []
    aliases_by_table = {}

    for condition in join_conditions:
        for column in condition.find_all(exp.Column):
            if column.table:
                aliases_by_table.setdefault(
                    resolve_table_name(column.table), column.table
                )

    for table in base_plans:
        scan_plan = Scan(
            table=table,
            alias=aliases_by_table.get(table)
        )
        dp[frozenset([table])] = {
            "plan": scan_plan,
            "cost": estimate_cost(scan_plan),
            "rows": estimate_rows(scan_plan),
        }

    return dp



def generate_two_table_candidates(tables, join_conditions, dp):
    """
    Generate the cheapest connected join plan for each pair of tables.

    Returns:
        A dictionary containing the best plan for each two-table subset.
    """
    candidates = {}

    for left_table, right_table in itertools.combinations(tables, 2):
        subset = frozenset([left_table, right_table])

        left_plan = dp[frozenset([left_table])]["plan"]
        right_plan = dp[frozenset([right_table])]["plan"]

        condition = find_join_condition(
            join_conditions,
            left_plan,
            right_plan
        )

        # Skip pairs that have no direct join condition.
        if condition is None:
            continue

        candidate_plan = Join(
            condition=condition,
            left=left_plan,
            right=right_plan
        )

        candidate_cost = estimate_cost(candidate_plan)
        candidate_rows = estimate_rows(candidate_plan)

        candidate_info = {
            "plan": candidate_plan,
            "cost": candidate_cost,
            "rows": candidate_rows,
        }

        # Keep the lowest-cost plan for this subset.
        if (
            subset not in candidates
            or candidate_cost < candidates[subset]["cost"]
        ):
            candidates[subset] = candidate_info

    return candidates



def dynamic_programming_join_search(base_plans, join_conditions):
    """
    Find the lowest-cost connected join plan using dynamic programming.
    Accept either alias-keyed base plans or the legacy list of table names.
    """
    if isinstance(base_plans, dict):
        tables = list(base_plans.keys())
        dp = initialize_dp_table(base_plans)
    else:
        # Backward compatibility for existing tests that pass table names.
        tables = list(base_plans)
        dp = initialize_dp_table(tables, join_conditions)

    for subset_size in range(2, len(tables) + 1):
        for subset_tuple in itertools.combinations(tables, subset_size):
            subset = frozenset(subset_tuple)
            best_candidate = None

            for left_size in range(1, subset_size):
                for left_tuple in itertools.combinations(
                    subset_tuple, left_size
                ):
                    left_subset = frozenset(left_tuple)
                    right_subset = subset - left_subset

                    # Avoid checking the same split in reverse.
                    if min(left_subset) > min(right_subset):
                        continue

                    if left_subset not in dp or right_subset not in dp:
                        continue

                    left_plan = dp[left_subset]["plan"]
                    right_plan = dp[right_subset]["plan"]

                    condition = find_join_condition(
                        join_conditions, left_plan, right_plan
                    )

                    # Never create a Cartesian join.
                    if condition is None:
                        continue

                    candidate_plan = Join(
                        condition=condition,
                        left=left_plan,
                        right=right_plan,
                    )

                    candidate_cost = estimate_cost(candidate_plan)
                    candidate_rows = estimate_rows(candidate_plan)

                    if (
                        best_candidate is None
                        or candidate_cost < best_candidate["cost"]
                    ):
                        best_candidate = {
                            "plan": candidate_plan,
                            "cost": candidate_cost,
                            "rows": candidate_rows,
                        }

            if best_candidate is not None:
                dp[subset] = best_candidate

    full_subset = frozenset(tables)

    if full_subset not in dp:
        raise ValueError(
            "Could not construct a connected join plan for all tables."
        )

    return dp[full_subset], dp
