try:
    from logical_plan import (
        Scan,
        Selection,
        Projection,
        Join,
    )
except ModuleNotFoundError:
    from scripts.logical_plan import (
        Scan,
        Selection,
        Projection,
        Join,
    )

def get_tables_in_subtree(node):
    """
    Return the set of table aliases/names contained
    in a logical-plan subtree.
    """

    if isinstance(node, Scan):
        return {node.alias if node.alias else node.table}

    if isinstance(node, Selection):
        return get_tables_in_subtree(node.child)

    if isinstance(node, Projection):
        return get_tables_in_subtree(node.child)

    if isinstance(node, Join):
        return (
            get_tables_in_subtree(node.left)
            | get_tables_in_subtree(node.right)
        )

    return set()

def get_referenced_tables(predicate):
    """
    Extract table aliases referenced by a predicate.

    Supports both:
    - sqlglot expression objects (used by Logical Plan)
    - predicate strings

    Examples:
        o.order_status = 'F'
            -> {'o'}

        c.cust_id = o.cust_id
            -> {'c', 'o'}
    """

    import sqlglot
    from sqlglot import exp

    # Phase 2 stores predicates as sqlglot expression objects.
    # Only parse the predicate if it is still a string.
    if isinstance(predicate, str):
        expression = sqlglot.parse_one(
            predicate,
            into=exp.Condition
        )
    else:
        expression = predicate

    tables = set()

    for column in expression.find_all(exp.Column):
        if column.table:
            tables.add(column.table)

    return tables

def push_selections(node):
    """
    Push Selection nodes as close to their base Scan
    as safely possible.
    """

    # --------------------------------------------------------
    # Selection
    # --------------------------------------------------------

    if isinstance(node, Selection):

        # First recursively optimize the child.
        node.child = push_selections(node.child)

        # Selection directly above a Join
        if isinstance(node.child, Join):

            predicate_tables = get_referenced_tables(
                node.predicate
            )

            left_tables = get_tables_in_subtree(
                node.child.left
            )

            right_tables = get_tables_in_subtree(
                node.child.right
            )

            # Predicate belongs only to LEFT side.
            if predicate_tables.issubset(left_tables):

                node.child.left = Selection(
                    predicate=node.predicate,
                    child=node.child.left
                )

                return push_selections(node.child)

            # Predicate belongs only to RIGHT side.
            elif predicate_tables.issubset(right_tables):

                node.child.right = Selection(
                    predicate=node.predicate,
                    child=node.child.right
                )

                return push_selections(node.child)

            # Predicate references both sides.
            # It must remain above the Join.
            else:
                return node

        return node

    # --------------------------------------------------------
    # Join
    # --------------------------------------------------------

    if isinstance(node, Join):

        node.left = push_selections(node.left)
        node.right = push_selections(node.right)

        return node

    # --------------------------------------------------------
    # Projection
    # --------------------------------------------------------

    if isinstance(node, Projection):

        node.child = push_selections(node.child)

        return node

    # --------------------------------------------------------
    # Scan
    # --------------------------------------------------------

    return node

def get_columns_from_expression(expression):
    """
    Extract column references from a sqlglot expression.

    Supports both sqlglot expression objects and strings.
    """

    import sqlglot
    from sqlglot import exp

    # Predicates from Logical Plan are already sqlglot expressions.
    if isinstance(expression, str):
        parsed = sqlglot.parse_one(
            expression,
            into=exp.Condition
        )
    else:
        parsed = expression

    columns = set()

    for column in parsed.find_all(exp.Column):
        if column.table:
            columns.add(f"{column.table}.{column.name}")
        else:
            columns.add(column.name)

    return columns

def get_projection_columns(node):
    """
    Return the columns explicitly requested by a Projection.
    """

    columns = set()

    if isinstance(node, Projection):

        for column in node.columns:

            column = column.strip()

            if "." in column:
                columns.add(column)

            else:
                columns.add(column)

    return columns

def get_join_columns(condition):
    """
    Extract all columns used by a join condition.
    """

    return get_columns_from_expression(condition)

def push_projections(node, needed_columns=None):
    """
    Push intermediate projections toward Scan nodes while
    preserving the original top-level Projection.
    """

    if needed_columns is None:
        needed_columns = set()

    # --------------------------------------------------------
    # Top-level Projection
    # --------------------------------------------------------

    if isinstance(node, Projection):

        # These are the columns required by the final output.
        output_columns = set(node.columns)

        # Push the requirements into the child.
        node.child = push_projections(
            node.child,
            output_columns
        )

        # IMPORTANT:
        # Keep the original top-level Projection.
        return node

    # --------------------------------------------------------
    # Selection
    # --------------------------------------------------------

    if isinstance(node, Selection):

        predicate_columns = get_columns_from_expression(
            node.predicate
        )

        needed = needed_columns | predicate_columns

        node.child = push_projections(
            node.child,
            needed
        )

        return node

    # --------------------------------------------------------
    # Join
    # --------------------------------------------------------

    if isinstance(node, Join):

        join_columns = get_join_columns(
            node.condition
        )

        needed = needed_columns | join_columns

        left_tables = get_tables_in_subtree(
            node.left
        )

        right_tables = get_tables_in_subtree(
            node.right
        )

        left_needed = set()
        right_needed = set()

        for column in needed:
            
            # Current scope assumes qualified column references in multi-table queries.
            # Unqualified columns are not assigned to a join branch here.
            if "." not in column:
                continue

            table = column.split(".", 1)[0]

            if table in left_tables:
                left_needed.add(column)

            if table in right_tables:
                right_needed.add(column)

        node.left = push_projections(
            node.left,
            left_needed
        )

        node.right = push_projections(
            node.right,
            right_needed
        )

        return node

    # --------------------------------------------------------
    # Scan
    # --------------------------------------------------------

    if isinstance(node, Scan):

        if needed_columns:

            table_columns = []

            for column in sorted(needed_columns):

                if "." in column:

                    table, column_name = column.split(
                        ".",
                        1
                    )

                    if table == node.alias:
                        table_columns.append(column)

                else:
                    table_columns.append(column)

            if table_columns:

                return Projection(
                    columns=table_columns,
                    child=node
                )

        return node

    return node

def remove_redundant_predicates(node):
    """
    Remove exact duplicate predicates and simple
    same-column subsumed predicates.
    """

    if isinstance(node, Projection):

        node.child = remove_redundant_predicates(
            node.child
        )

        return node

    if isinstance(node, Join):

        node.left = remove_redundant_predicates(
            node.left
        )

        node.right = remove_redundant_predicates(
            node.right
        )

        return node

    if isinstance(node, Selection):

        # First simplify the child.
        node.child = remove_redundant_predicates(
            node.child
        )

        # Collect consecutive Selection nodes.
        selections = []
        current = node

        while isinstance(current, Selection):

            selections.append(current.predicate)
            current = current.child

        # Nothing to simplify.
        if len(selections) <= 1:
            return node

        # Remove exact duplicates while preserving order.
        unique = []

        for predicate in selections:

            if predicate not in unique:
                unique.append(predicate)

        selections = unique

        # ----------------------------------------------------
        # Simple same-column comparison subsumption
        # ----------------------------------------------------

        import sqlglot
        from sqlglot import exp

        removable = set()

        for i in range(len(selections)):

            for j in range(i + 1, len(selections)):

                try:
                    a = sqlglot.parse_one(
                        selections[i],
                        into=exp.Condition
                    )

                    b = sqlglot.parse_one(
                        selections[j],
                        into=exp.Condition
                    )

                    if not isinstance(a, exp.Binary):
                        continue

                    if not isinstance(b, exp.Binary):
                        continue

                    a_column = a.left
                    b_column = b.left

                    if not isinstance(
                        a_column,
                        exp.Column
                    ):
                        continue

                    if not isinstance(
                        b_column,
                        exp.Column
                    ):
                        continue

                    if (
                        a_column.sql()
                        != b_column.sql()
                    ):
                        continue

                    a_value = a.right
                    b_value = b.right

                    if not isinstance(
                        a_value,
                        exp.Literal
                    ):
                        continue

                    if not isinstance(
                        b_value,
                        exp.Literal
                    ):
                        continue

                    if not (
                        a_value.is_number
                        and b_value.is_number
                    ):
                        continue

                    av = float(a_value.this)
                    bv = float(b_value.this)

                    a_op = a.key
                    b_op = b.key

                    # x > A AND x > B
                    if a_op == "gt" and b_op == "gt":

                        if av >= bv:
                            removable.add(j)
                        else:
                            removable.add(i)

                    # x >= A AND x >= B
                    elif (
                        a_op == "gte"
                        and b_op == "gte"
                    ):

                        if av >= bv:
                            removable.add(j)
                        else:
                            removable.add(i)

                    # x < A AND x < B
                    elif a_op == "lt" and b_op == "lt":

                        if av <= bv:
                            removable.add(j)
                        else:
                            removable.add(i)

                    # x <= A AND x <= B
                    elif (
                        a_op == "lte"
                        and b_op == "lte"
                    ):

                        if av <= bv:
                            removable.add(j)
                        else:
                            removable.add(i)

                    # x = A AND x = A
                    elif (
                        a_op == "eq"
                        and b_op == "eq"
                        and av == bv
                    ):

                        removable.add(j)

                except Exception:
                    continue

        selections = [
            predicate
            for index, predicate
            in enumerate(selections)
            if index not in removable
        ]

        # Rebuild Selection stack.
        result = current

        for predicate in reversed(selections):

            result = Selection(
                predicate=predicate,
                child=result
            )

        return result

    return node

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