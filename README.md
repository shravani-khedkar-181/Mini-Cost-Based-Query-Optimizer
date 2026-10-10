# Mini Cost-Based Query Optimizer

A database systems project that explores query optimization using PostgreSQL and a custom query optimizer.

## Project Overview

This project is designed to study how a query optimizer can estimate query costs, choose execution plans, and compare its decisions with PostgreSQL's optimizer.

The project is being developed in multiple phases, starting with database setup and statistics collection.

## Project Structure

```text
mini-query-optimizer/
│
├── data/                    # Local TPC-H .tbl files (not committed)
├── sql/                     # Database schema and SQL files
├── stats/                   # Collected database statistics
├── scripts/                 # Project utility scripts
├── optimizer/               # Custom query optimizer
├── tests/                   # Project tests
├── dashboard/               # Future visualization/dashboard
│
├── .gitignore
├── requirements.txt
└── README.md

```

## Requirements

The project currently uses:

* Windows
* WSL2
* Ubuntu 24.04
* PostgreSQL
* Python 3.11 or newer
* Git
* VS Code

Python packages:

* `psycopg2-binary`
* `sqlalchemy`
* `pandas`
* `sqlglot`

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd mini-query-optimizer

```

### 2. Create a Python virtual environment

On Windows PowerShell:

```powershell
python -m venv venv

```

Activate it:

```powershell
venv\Scripts\activate

```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt

```

## Database Setup

Create a PostgreSQL database named `mini_optimizer`.

Then load the schema:

```bash
psql -U postgres -d mini_optimizer -f sql\schema.sql

```

The project currently uses five tables:

* `customer`
* `orders`
* `lineitem`
* `supplier`
* `nation`

## TPC-H Dataset

The project uses the TPC-H benchmark dataset.

### Dataset configuration

* **Dataset:** TPC-H
* **Generator:** `dbgen`
* **Scale Factor:** 0.01
* **Source:** `electrum/tpch-dbgen`

**Tables used:**

* `customer`
* `orders`
* `lineitem`
* `supplier`
* `nation`

The `.tbl` files are intentionally not committed to Git. Each developer should generate the dataset locally using the same TPC-H `dbgen` process at Scale Factor 0.01.

The project's `.gitignore` contains:

```text
data/*.tbl

```

### Load the TPC-H Data

After generating the `.tbl` files, copy the required files into `data/`:

1. `customer.tbl`
2. `orders.tbl`
3. `lineitem.tbl`
4. `supplier.tbl`
5. `nation.tbl`

The files should have their trailing `|` delimiter removed before loading into PostgreSQL.

Load the files using PostgreSQL `\copy` commands. For example:

```sql
\copy nation FROM 'C:/Users/<username>/Desktop/mini-query-optimizer/data/nation.tbl' WITH (FORMAT csv, DELIMITER '|');

```

Repeat for the other four tables.

Expected SF 0.01 row counts for this generated dataset are:

| Table | Row Count |
| --- | --- |
| `nation` | 25 |
| `customer` | 1,500 |
| `supplier` | 100 |
| `orders` | 15,000 |
| `lineitem` | 60,175 |

## Collect PostgreSQL Statistics

After loading the data, connect to the database:

```bash
psql -U postgres -d mini_optimizer

```

Run:

```sql
ANALYZE;

```

Then collect the project's baseline statistics:

```bash
python scripts\collect_stats.py

```

The script creates `stats/baseline_stats.json`.

The statistics include:

* Table row counts
* Column distinct-value estimates
* Column null fractions

These statistics provide the baseline information that will later be used by the custom query optimizer.

## Environment Variables

The database password should not be stored directly in source code. `collect_stats.py` reads the PostgreSQL password from `POSTGRES_PASSWORD`.

For a PowerShell session:

```powershell
$env:POSTGRES_PASSWORD="your-password"

```

Do not commit your password to GitHub.

## Current Phase

### Phase 1 — Database and Statistics Setup (Completed)

* [x] WSL2 setup
* [x] TPC-H `dbgen` setup
* [x] TPC-H SF 0.01 dataset generation
* [x] PostgreSQL database creation
* [x] PostgreSQL schema creation
* [x] TPC-H data loading
* [x] Row-count verification
* [x] Join relationship verification
* [x] PostgreSQL `ANALYZE`
* [x] Baseline statistics collection

### Phase 2 — SQL Parser & Logical Plan Builder

The optimizer uses SQLGlot to parse SQL queries and convert
the resulting AST into an internal relational algebra tree.

Supported:
- SELECT
- FROM
- INNER JOIN
- JOIN ... ON
- WHERE
- AND predicates
- Column projections
- Table aliases

Not currently supported:
- Subqueries
- OUTER JOIN
- UNION / INTERSECT / EXCEPT
- Window functions
- Nested queries

## Phase 3 — Heuristic Rewrite Engine

**Status: Completed ✅**

Implemented and tested three heuristic query-rewrite rules:

* **Selection Pushdown** — moves filters closer to their relevant base tables.
* **Projection Pushdown** — keeps only required columns near the scans.
* **Redundant Predicate Removal** — removes duplicate and subsumed predicates.

### Verification

* Q1–Q10 passed the complete rewrite pipeline.
* Q11 verified redundant predicate removal:
  `acct_balance > 1000 AND acct_balance > 5000` → `acct_balance > 5000`
* Both-side predicates were correctly kept above the join.
* Before/after logical plans were successfully generated.

### Main Files

* `scripts/rewrite_engine.py`
* `scripts/test_phase3.py`
* `scripts/test_selection_pushdown.py`
* `scripts/test_projection_pushdown.py`
* `scripts/test_redundant_predicates.py`

## Phase 4: Cost Estimation Module — Completed

Implemented a cost estimation model using Phase 1 statistics.

### Completed

* Loaded `baseline_stats.json` for row counts and distinct values.
* Implemented equality, range, and join selectivity estimation.
* Added alias-to-table resolution (`o` → `orders`, etc.).
* Implemented recursive row-count estimation for Scan, Selection, Projection, and Join.
* Implemented recursive query cost estimation.
* Validated Q1–Q10 using `test_phase4.py`.
* Compared original and Phase 3 rewritten plan costs.

### Results

* Q5 cost reduction: **65.94%**
* Q7 cost reduction: **83.60%**
* Q10 cost reduction: **89.57%**
* Single-table estimates were hand-verified against Phase 1 statistics.

### Scope

The model uses textbook selectivity formulas and a simplified nested-loop-style cost model. Histograms, buffer-pool effects, and detailed physical I/O costs are outside the project scope.

**Phase 4 Status: Complete ✓**

## Phase 5: Dynamic Programming Join-Order Optimization

### Overview
Phase 5 implements a dynamic programming (DP) algorithm to search for a low-cost join order for multi-table SQL queries. Instead of following only the join order produced by the SQL parser, the optimizer evaluates alternative connected join combinations using estimated cardinalities and costs.

### Implementation
The implementation is located in `scripts/join_order_search.py`.

Key components:
- **Join graph extraction:** Extracts base-table plans and join predicates from the logical plan.
- **Predicate preservation:** Retains single-table selections and projections when initializing the DP search, so filters are reflected in base-plan estimates.
- **Dynamic programming search:** Evaluates alternative connected join orders and retains the lowest-cost plan for each subset of tables.
- **Join-condition validation:** Ensures joins connect the required table subsets and rejects disconnected join combinations that would otherwise require a Cartesian product.
- **Cost and cardinality estimation:** Uses the existing cost model to compare candidate plans.

### Testing
Run the Phase 5 tests from the project root:

```powershell
python scripts\test_phase5.py
python scripts\test_phase5_filtered.py
```

The tests cover two-table and three-table joins, join-order cost comparison, multiple join predicates, disconnected join graphs, join-condition validation, and filtered multi-table queries.

### Example Results

| Query | Tables | Estimated Rows | Estimated Cost |
|---|---:|---:|---:|
| Q7 | 3 | 6,686.11 | 12,452.86 |
| Q10 | 5 | 1,337.22 | 7,474.11 |

These values are estimates produced by the current cost model, not measured execution times.

### Observations
- **Q7:** The selected DP plan retained the original effective join order.
- **Q10:** The selected plan joined the filtered `nation` and `supplier` relations early. The estimated cardinality of `nation` after applying `regionid = 1` was five rows.
- The selected join trees were printed and inspected to verify that the DP search retained the single-table filters.

### Phase 5 Status
The existing Phase 5 test suite passed, and the filtered-query checks for Q7 and Q10 produced join plans with estimated costs and cardinalities.

A quantified cost improvement over the original join order should only be reported after both plans are evaluated using the same cost model.

**Phase 5 Status: Complete ✓**

## Future Phases

Planned project phases include:
* **Phase 6 — PostgreSQL Comparison:** Compare the custom optimizer's decisions against PostgreSQL's optimizer.
* **Phase 7 — Testing and Evaluation:** Evaluate optimizer accuracy and performance using TPC-H queries.
* **Phase 8 — Dashboard:** Build a dashboard for visualizing query plans, estimated cardinalities, estimated costs, PostgreSQL plans, and optimizer comparisons.

## Development Notes

* TPC-H data files are local development data and should not be committed to the repository.
* The project uses the same TPC-H generator configuration across team members so that everyone works with reproducible data.
* When making changes, keep generated data and personal credentials out of Git.

