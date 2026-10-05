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

## Future Phases

Planned project phases include:

* **Phase 2 — SQL Parsing:** Parse SQL queries and identify tables, joins, filters, projections, and predicates.
* **Phase 3 — Cardinality Estimation:** Develop methods to estimate intermediate result sizes using collected statistics.
* **Phase 4 — Cost Estimation:** Estimate the cost of alternative query execution plans.
* **Phase 5 — Query Plan Generation:** Generate and compare alternative execution plans.
* **Phase 6 — PostgreSQL Comparison:** Compare the custom optimizer's decisions against PostgreSQL's optimizer.
* **Phase 7 — Testing and Evaluation:** Evaluate optimizer accuracy and performance using TPC-H queries.
* **Phase 8 — Dashboard:** Build a dashboard for visualizing query plans, estimated cardinalities, estimated costs, PostgreSQL plans, and optimizer comparisons.

## Development Notes

* TPC-H data files are local development data and should not be committed to the repository.
* The project uses the same TPC-H generator configuration across team members so that everyone works with reproducible data.
* When making changes, keep generated data and personal credentials out of Git.

