import json
import os
import psycopg2

DB_NAME = "mini_optimizer"
DB_USER = "postgres"
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = "localhost"
DB_PORT = "5432"

TABLES = [
    "customer",
    "orders",
    "lineitem",
    "supplier",
    "nation",
]


def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def collect_stats():
    conn = get_connection()
    cursor = conn.cursor()
    stats = {}

    for table in TABLES:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        row_count = cursor.fetchone()[0]

        stats[table] = {
            "row_count": row_count,
            "columns": {},
        }

        cursor.execute(
            """
            SELECT
                attname,
                n_distinct,
                null_frac
            FROM pg_stats
            WHERE tablename = %s
            ORDER BY attname;
            """,
            (table,),
        )

        for column_name, n_distinct, null_frac in cursor.fetchall():
            stats[table]["columns"][column_name] = {
                "distinct": n_distinct,
                "null_frac": null_frac,
            }

    cursor.close()
    conn.close()

    return stats


def main():
    stats = collect_stats()
    project_root = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    stats_dir = os.path.join(project_root, "stats")
    os.makedirs(stats_dir, exist_ok=True)

    output_file = os.path.join(stats_dir, "baseline_stats.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print(f"Statistics written to: {output_file}")


if __name__ == "__main__":
    main()