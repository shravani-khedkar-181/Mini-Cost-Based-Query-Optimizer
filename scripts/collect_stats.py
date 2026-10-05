import json
import psycopg2
from pathlib import Path


# --------------------------------------------------
# Database configuration
# --------------------------------------------------

DB_NAME = "mini_optimizer"
DB_USER = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"


# --------------------------------------------------
# Tables and columns for our optimizer
# --------------------------------------------------

TABLE_COLUMNS = {
    "customer": [
        "cust_id",
        "nationid",
        "acct_balance",
        "market_segment"
    ],
    "orders": [
        "order_id",
        "cust_id",
        "order_status",
        "total_price",
        "order_date",
        "order_priority"
    ],
    "lineitem": [
        "order_id",
        "supplierid",
        "quantity",
        "extended_price",
        "discount",
        "tax",
        "return_flag",
        "line_status",
        "ship_date",
        "commit_date",
        "receipt_date"
    ],
    "supplier": [
        "supplierid",
        "nationid",
        "acct_balance"
    ],
    "nation": [
        "nationid",
        "regionid",
        "name"
    ]
}


# --------------------------------------------------
# Connect to PostgreSQL
# --------------------------------------------------

def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        host=DB_HOST,
        port=DB_PORT
    )


# --------------------------------------------------
# Collect statistics
# --------------------------------------------------

def collect_statistics():
    conn = get_connection()
    cursor = conn.cursor()

    statistics = {}

    for table, columns in TABLE_COLUMNS.items():

        print(f"Collecting statistics for {table}...")

        # Total row count
        cursor.execute(
            f"SELECT COUNT(*) FROM {table};"
        )

        row_count = cursor.fetchone()[0]

        statistics[table] = {
            "row_count": row_count,
            "columns": {}
        }

        for column in columns:

            # Distinct values and NULL count
            cursor.execute(
                f"""
                SELECT
                    COUNT(DISTINCT {column}),
                    COUNT(*) - COUNT({column})
                FROM {table};
                """
            )

            distinct_count, null_count = cursor.fetchone()

            # Min/max
            cursor.execute(
                f"""
                SELECT
                    MIN({column}),
                    MAX({column})
                FROM {table};
                """
            )

            min_value, max_value = cursor.fetchone()

            statistics[table]["columns"][column] = {
                "distinct": distinct_count,
                "nulls": null_count,
                "min": str(min_value) if min_value is not None else None,
                "max": str(max_value) if max_value is not None else None
            }

    cursor.close()
    conn.close()

    return statistics


# --------------------------------------------------
# Save statistics
# --------------------------------------------------

def main():

    statistics = collect_statistics()

    output_path = Path("stats/baseline_stats.json")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            statistics,
            file,
            indent=2
        )

    print()
    print("Statistics collection complete.")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()