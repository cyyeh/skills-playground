# System Analysis: DuckDB

## Metadata
- **Name:** DuckDB
- **Category:** Embedded Analytical Database (OLAP)
- **Official URL:** https://duckdb.org
- **GitHub:** https://github.com/duckdb/duckdb
- **License:** MIT
- **Latest Version:** 1.5.1 (March 23, 2026)
- **Created By:** Mark Raasveldt and Hannes Muhleisen at CWI (Centrum Wiskunde & Informatica), Amsterdam

---

## Overview
<!-- level: beginner -->

DuckDB is an in-process analytical database management system. Think of it as **"SQLite for analytics"** -- just as SQLite gives you a zero-configuration embedded database for transactional workloads, DuckDB gives you the same simplicity but optimized for analytical queries that scan, aggregate, and join large datasets.

### What Problem Does It Solve?

Before DuckDB, data analysts and engineers faced an awkward choice:

- **Use SQLite or Postgres** -- great for transactional data, but painfully slow when you need to aggregate millions of rows or join large tables.
- **Use a data warehouse (BigQuery, Snowflake, Redshift)** -- powerful analytics, but requires cloud infrastructure, network round-trips, and costs money per query.
- **Use pandas/Polars in Python** -- flexible, but you lose SQL's expressiveness and hit memory limits on larger datasets.

DuckDB fills the gap: a single-file, zero-dependency database that runs inside your process and handles analytical workloads at remarkable speed. You can query a 10GB Parquet file on your laptop in seconds, with no server to install, no configuration to manage, and no data to upload.

### Who Is It For?

- **Data analysts** who want to query CSV, Parquet, or JSON files with SQL
- **Data engineers** building ETL pipelines without heavyweight infrastructure
- **Data scientists** who need SQL alongside Python/R DataFrames
- **Application developers** embedding analytics into their products
- **Anyone** who wants to explore data quickly without setting up a database server

### Core Value Proposition

| Trait | What It Means |
|-------|---------------|
| **In-process** | Runs inside your application -- no separate server process |
| **Zero dependencies** | Single binary or library, compiles to a header + implementation file |
| **Columnar storage** | Data stored by column, not by row -- ideal for analytical queries |
| **Vectorized execution** | Processes batches of 2,048 values at once for CPU-cache-friendly performance |
| **Rich SQL** | Full SQL support including window functions, CTEs, lateral joins, and more |
| **Multi-format** | Directly queries Parquet, CSV, JSON, Iceberg, and remote files (S3/HTTP) |
| **ACID compliant** | Persistent storage with transactions, even in embedded mode |

---

## Core Concepts
<!-- level: beginner -->

### 1. In-Process Database

**Analogy:** DuckDB is like a calculator built into your spreadsheet app. Instead of opening a separate calculator program, typing numbers in, and copying results back, the calculator runs right inside Excel. There's no separate process, no network connection -- it's just there, instantly available.

Technically, DuckDB runs as a library loaded into your application's process. When your Python script does `import duckdb`, the entire database engine is now part of your script. This eliminates the client-server overhead that databases like PostgreSQL require.

### 2. Columnar Storage

**Analogy:** Imagine a filing cabinet. A row-based database stores each person's complete file in one folder -- name, age, salary, address all together. To calculate the average salary, you'd open every single folder. A columnar database is like having one drawer labeled "Salaries" containing just the salary values for everyone. To compute the average, you open one drawer and scan straight through.

DuckDB stores data column-by-column rather than row-by-row. This means:
- **Compression is better** -- similar values in the same column compress efficiently (e.g., a column of country codes)
- **Scans are faster** -- analytical queries that aggregate one or two columns don't need to read the other 50 columns
- **CPU caches are happier** -- processing contiguous arrays of the same type fits modern CPU architectures perfectly

### 3. Vectorized Execution

**Analogy:** Imagine you're a teacher grading exams. Row-at-a-time processing is like grading one student's entire exam before moving to the next. Vectorized execution is like grading Question 1 for all students, then Question 2 for all students. Your brain stays in "Question 1 mode," you get faster, and you spot patterns.

DuckDB processes data in vectors (batches) of 2,048 values. Each operation -- filtering, summing, comparing -- runs over the entire vector at once using tight loops that the CPU can optimize with SIMD (Single Instruction, Multiple Data) instructions. This dramatically reduces the per-row overhead of traditional row-at-a-time engines.

### 4. Extensions

**Analogy:** Extensions are like apps on your phone. Your phone (DuckDB) does a lot out of the box, but when you need GPS navigation (spatial queries), cloud storage access (httpfs), or to read a specific file format (Iceberg), you install the relevant app. Core extensions auto-install when you first use them.

DuckDB's extension system allows adding:
- New file formats (Parquet, Iceberg, Lance, Delta Lake)
- Remote access (S3, HTTP, Azure Blob Storage)
- Domain-specific functionality (spatial/GIS, full-text search)
- Database connectors (PostgreSQL, MySQL, SQLite scanner)

### 5. Data Virtualization (Zero-Copy Querying)

**Analogy:** Instead of photocopying a library book to read it at home, DuckDB lets you read the book right on the shelf. It can query Parquet files, CSV files, Pandas DataFrames, and even remote S3 objects directly without importing or copying the data first.

This is powered by DuckDB's "replacement scan" feature, which intercepts references to external objects (like a pandas DataFrame variable name in SQL) and transparently reads them in-place.

### 6. Single-File Persistence

**Analogy:** Just like a SQLite `.db` file or an Excel `.xlsx` file, a DuckDB database is a single file on disk. You can email it, `scp` it to a server, or check it into version control. No WAL directories, no tablespaces, no configuration files -- just one file.

DuckDB databases use the `.duckdb` extension by default. They support ACID transactions via a custom MVCC (Multi-Version Concurrency Control) implementation and allow multiple concurrent readers with a single writer.

---

## Architecture
<!-- level: intermediate -->

### System Overview

DuckDB's architecture is a pipeline that transforms SQL text into efficiently executed operations on columnar data:

```
SQL Query
    │
    ▼
┌─────────────┐
│   Parser     │  SQL text → Abstract Syntax Tree (AST)
└──────┬──────┘
       ▼
┌─────────────┐
│   Binder     │  Resolve names, types, and schemas
└──────┬──────┘
       ▼
┌─────────────────┐
│ Logical Planner  │  AST → Logical operators (scan, filter, join, aggregate)
└──────┬──────────┘
       ▼
┌─────────────────┐
│   Optimizer      │  Rewrite rules, join ordering, predicate pushdown
└──────┬──────────┘
       ▼
┌──────────────────┐
│ Physical Planner  │  Logical plan → Physical operators with execution strategies
└──────┬───────────┘
       ▼
┌──────────────────┐
│ Execution Engine  │  Vectorized, parallel, pipeline-based execution
└──────┬───────────┘
       ▼
    Results
```

### Why Each Component Exists

**Parser** -- DuckDB includes its own hand-written parser (originally derived from PostgreSQL's parser, now heavily modified). In v1.5.0, an experimental PEG parser was added to provide better error messages with suggestions. The parser exists separately because SQL syntax is complex and evolving -- DuckDB adds syntax extensions like `COLUMNS(*)`, `EXCLUDE`, and `FROM-first` syntax.

**Binder** -- Resolves table names, column references, and function calls against the catalog. This is where DuckDB determines that `SELECT salary FROM employees` refers to a specific column in a specific table, resolves types, and validates the query. Without binding, the optimizer would be working with unresolved names.

**Optimizer** -- The optimizer is critical for analytical workloads because query plans that work fine on 100 rows can be catastrophically slow on 100 million. DuckDB's optimizer applies:
- **Predicate pushdown** -- Push filters as close to the scan as possible to read less data
- **Column pruning** -- Only read columns that are actually needed
- **Join ordering** -- Choose the order that minimizes intermediate result sizes
- **Common subexpression elimination** -- Avoid recomputing the same expressions
- **Top-N optimization** -- For `ORDER BY ... LIMIT N`, avoid sorting the entire dataset

**Execution Engine** -- The vectorized, pipeline-based engine is the heart of DuckDB's performance. Instead of pulling one row at a time through a tree of operators (the Volcano model), DuckDB pushes vectors of data through pipelines. Each pipeline is a chain of operators that can execute without materializing intermediate results, and multiple pipelines execute in parallel across CPU cores.

### Storage Layout

DuckDB organizes persistent data into **row groups** (chunks of ~122,000 rows). Within each row group, data is stored column-by-column with:

- **Compression** -- Each column segment is independently compressed using the best algorithm for its data distribution (constant, dictionary, RLE, bitpacking, FSST for strings, ALP for floats, Chimp for doubles)
- **Zone maps (min/max indexes)** -- Each column segment stores its minimum and maximum values. When a query filters on `WHERE date > '2025-01-01'`, entire row groups where `max(date) < '2025-01-01'` are skipped entirely without reading any data.
- **Partial decompression** -- DuckDB can operate on compressed data during execution (e.g., dictionary vectors), deferring decompression until necessary.

### Parallelism Model

DuckDB automatically parallelizes queries across all available CPU cores:

1. **Morsel-driven parallelism** -- Row groups are divided into "morsels" assigned to worker threads. Each thread processes its morsel independently through the pipeline.
2. **No user configuration** -- Parallelism is automatic. No `SET parallel_workers` or partitioning required.
3. **Parallel-aware operators** -- Hash joins, aggregations, and sorts are all designed for parallel execution with shared hash tables and merge steps.
4. **Parallel I/O** -- Even CSV and Parquet file reading is parallelized, with multiple threads scanning different portions of a file.

### Concurrency Model

DuckDB uses a **single-writer, multiple-reader** model:
- Multiple connections can read simultaneously
- Only one connection can write at a time
- This is a deliberate design choice -- DuckDB is not designed for high-concurrency OLTP workloads with many concurrent writers
- In v1.5.0, non-blocking checkpointing was added, allowing reads to continue during checkpoint operations (17% throughput improvement on TPC-H)

### Memory Management

- **Buffer manager** -- DuckDB manages its own buffer pool, paging data in and out of memory as needed
- **Spill to disk** -- When intermediate results exceed available memory, DuckDB spills to temporary files on disk rather than crashing with an OOM error
- **Streaming execution** -- Where possible, operators stream data through the pipeline without materializing entire intermediate results
- **Configurable memory limit** -- Users can set `SET memory_limit = '4GB'` to control DuckDB's memory usage

---

## How It Works
<!-- level: intermediate -->

### Query Execution: A Walkthrough

Let's trace what happens when you run:

```sql
SELECT region, SUM(amount) as total
FROM sales
WHERE year = 2025
GROUP BY region
ORDER BY total DESC
LIMIT 5;
```

**Step 1: Parse & Bind**
The SQL is parsed into an AST, then the binder resolves `sales` to the table in the catalog, confirms `region`, `amount`, and `year` are valid columns, and determines their types.

**Step 2: Logical Plan**
```
Limit(5)
  └── Sort(total DESC)
        └── Aggregate(GROUP BY region, SUM(amount))
              └── Filter(year = 2025)
                    └── Scan(sales)
```

**Step 3: Optimize**
The optimizer pushes the filter `year = 2025` into the scan operator. If `year` has zone maps, entire row groups where `max(year) < 2025` or `min(year) > 2025` are eliminated before reading any data. Column pruning ensures only `region`, `amount`, and `year` are read (not any other columns in the table). The `ORDER BY ... LIMIT 5` is recognized as a Top-5 operation, using a heap instead of a full sort.

**Step 4: Physical Plan & Pipeline Construction**
The optimizer creates two pipelines:

- **Pipeline 1:** Scan → Filter → Aggregate (builds the hash table for GROUP BY)
- **Pipeline 2:** Finalize Aggregate → Top-5 Sort → Result

Pipeline 1 is the heavy work -- it scans all matching row groups in parallel, filters, and inserts into a shared hash table partitioned by thread.

**Step 5: Vectorized Execution**
Each thread in Pipeline 1:
1. Reads a morsel (batch of row groups)
2. Decompresses only `year`, `region`, `amount` columns into vectors of 2,048 values
3. Applies the filter `year = 2025`, producing a selection vector (bitset of matching rows)
4. For matching rows, hashes `region` and updates the running SUM in the hash table
5. Repeats until its morsel is done, then grabs the next morsel

Pipeline 2 merges per-thread hash tables, runs Top-5 selection, and returns results.

### The Vector Format

DuckDB's internal data representation uses several vector types for efficiency:

| Vector Type | Purpose | Example |
|-------------|---------|---------|
| **Flat** | Standard contiguous array | A column of integers read from storage |
| **Constant** | Single value repeated for all rows | The literal `2025` in `WHERE year = 2025` |
| **Dictionary** | Index into a smaller value set | Dictionary-compressed string column |
| **Sequence** | Offset + increment | Row IDs (`0, 1, 2, 3, ...`) |

Operators output one of these types, and the next operator can handle any type through the **Unified Vector Format** -- a common abstraction that avoids combinatorial explosion of type-pair handling in operations.

**String handling** is particularly clever: strings of 12 bytes or fewer are inlined directly into the vector (no pointer indirection). Larger strings store a pointer plus a 4-byte prefix -- the prefix allows many string comparisons (e.g., `WHERE name > 'M'`) to short-circuit without following the pointer.

### Compression Algorithms

DuckDB automatically selects the best compression for each column segment:

| Algorithm | Best For | How It Works |
|-----------|----------|--------------|
| **Constant** | Columns with a single value | Stores one value for the whole segment |
| **Dictionary** | Low-cardinality columns | Maps values to small integer codes |
| **RLE (Run-Length Encoding)** | Sorted or clustered data | Stores `(value, count)` pairs |
| **Bitpacking** | Integers with small range | Uses fewer bits per value (e.g., 4-bit for values 0-15) |
| **FSST (Fast Static Symbol Table)** | String columns | Compresses common substrings into short codes |
| **ALP (Adaptive Lossless floating-Point)** | Float/double columns | Exploits patterns in floating-point data |
| **Chimp** | Time-series doubles | XOR-based compression for sequential doubles |

The compression analyzer runs during data loading and picks the algorithm that yields the best compression ratio for each column segment independently.

### Direct File Querying

One of DuckDB's most powerful features is querying files directly without loading them first:

```sql
-- Query a local Parquet file
SELECT * FROM 'sales_2025.parquet' WHERE region = 'APAC';

-- Query a CSV with auto-detection
SELECT * FROM read_csv('data.csv');

-- Query Parquet files on S3
SELECT * FROM 's3://my-bucket/data/*.parquet';

-- Query a remote CSV over HTTP
SELECT * FROM 'https://example.com/data.csv';
```

DuckDB's multi-hypothesis CSV parser automatically infers column types, delimiters, and headers by examining the file. For Parquet files, it leverages Parquet metadata (row group statistics, page indexes) to push down filters and skip irrelevant data before reading it.

---

## Implementation Details
<!-- level: advanced -->

### Getting Started

**Installation:**

```bash
# Python
pip install duckdb

# CLI (Python-based installer)
pip install duckdb-cli

# macOS (Homebrew)
brew install duckdb

# Node.js
npm install duckdb

# Or download a binary from https://duckdb.org/docs/installation/
```

**First query (CLI):**

```sql
$ duckdb
v1.5.1
Enter ".help" for usage hints.
Connected to a transient in-memory database.

D SELECT 42 AS answer;
┌────────┐
│ answer │
│ int32  │
├────────┤
│     42 │
└────────┘
```

**First query (Python):**

```python
import duckdb

# In-memory (default)
con = duckdb.connect()

# Query a Parquet file directly
result = con.sql("SELECT region, SUM(amount) FROM 'sales.parquet' GROUP BY region")
print(result.fetchdf())  # Returns a pandas DataFrame

# Or use the relation API
con.sql("SELECT * FROM 'data.csv' WHERE age > 30").show()
```

**Persistent database:**

```python
# Creates/opens a file-based database
con = duckdb.connect('my_analytics.duckdb')
con.sql("CREATE TABLE events AS SELECT * FROM 'events_*.parquet'")
con.sql("SELECT event_type, COUNT(*) FROM events GROUP BY 1").show()
con.close()
```

### Configuration & Tuning

```sql
-- Memory limit (default: 80% of system RAM)
SET memory_limit = '8GB';

-- Thread count (default: all cores)
SET threads = 4;

-- Temp directory for spill-to-disk (default: .tmp in current directory)
SET temp_directory = '/fast-ssd/duckdb-tmp';

-- Enable progress bar for long queries
SET enable_progress_bar = true;

-- Preserve insertion order (disable for faster bulk loads)
SET preserve_insertion_order = false;
```

### Python Integration Patterns

```python
import duckdb
import pandas as pd

# Zero-copy query on a pandas DataFrame
df = pd.read_csv('large_file.csv')
result = duckdb.sql("SELECT category, AVG(price) FROM df GROUP BY category")

# Chain operations with the relation API
(duckdb
    .read_parquet('s3://bucket/data/*.parquet')
    .filter("year = 2025")
    .aggregate("region, SUM(revenue) AS total")
    .order("total DESC")
    .limit(10)
    .show())

# Export results to different formats
duckdb.sql("SELECT * FROM 'input.csv' WHERE status = 'active'") \
      .write_parquet('output.parquet')

# Use as a persistent analytics store
con = duckdb.connect('analytics.duckdb')
con.sql("""
    CREATE OR REPLACE TABLE daily_metrics AS
    SELECT date_trunc('day', timestamp) AS day,
           COUNT(*) AS events,
           COUNT(DISTINCT user_id) AS users
    FROM read_parquet('events_*.parquet')
    GROUP BY 1
""")
```

### Advanced SQL Features

```sql
-- Window functions
SELECT employee, department, salary,
       RANK() OVER (PARTITION BY department ORDER BY salary DESC) as rank
FROM employees;

-- COLUMNS expression (DuckDB-specific) -- apply operations to multiple columns
SELECT MIN(COLUMNS('amount_*')), MAX(COLUMNS('amount_*'))
FROM transactions;

-- EXCLUDE / REPLACE in SELECT
SELECT * EXCLUDE (internal_id, debug_flag)
FROM users;

-- Recursive CTEs
WITH RECURSIVE org_tree AS (
    SELECT id, name, manager_id, 0 AS depth
    FROM employees WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.name, e.manager_id, t.depth + 1
    FROM employees e JOIN org_tree t ON e.manager_id = t.id
)
SELECT * FROM org_tree;

-- ASOF joins (time-series aligned joins)
SELECT t.*, p.price
FROM trades t ASOF JOIN prices p
ON t.ticker = p.ticker AND t.timestamp >= p.timestamp;

-- List comprehensions and lambdas
SELECT list_transform([1, 2, 3, 4], lambda x: x * x);
-- Note: Arrow syntax (x -> x * x) is deprecated as of v1.5.0

-- PIVOT / UNPIVOT
PIVOT sales ON region USING SUM(amount);

-- FROM-first syntax (DuckDB-specific)
FROM sales SELECT region, SUM(amount) WHERE year = 2025 GROUP BY region;
```

### Extension Management

```sql
-- Install and load an extension
INSTALL httpfs;
LOAD httpfs;

-- Most core extensions auto-load when needed:
SELECT * FROM 's3://bucket/data.parquet';  -- auto-loads httpfs

-- Configure S3 credentials
SET s3_region = 'us-east-1';
SET s3_access_key_id = 'AKIA...';
SET s3_secret_access_key = '...';

-- Or use AWS credential chain
SET s3_use_credential_provider = 'credential_chain';

-- List installed extensions
SELECT * FROM duckdb_extensions();

-- Key extensions:
-- httpfs      -- S3, HTTP, and HTTPS file access
-- parquet     -- Parquet reader/writer (bundled by default)
-- iceberg     -- Apache Iceberg table support
-- spatial     -- GIS/geometry functions (GEOMETRY type is now core in v1.5.0)
-- postgres    -- Scan PostgreSQL tables directly
-- sqlite      -- Scan SQLite databases directly
-- json        -- JSON file reader (bundled by default)
-- excel       -- Read/write Excel files
-- lance       -- Lance lakehouse format (new in v1.5.1)
-- ducklake    -- DuckLake catalog/lakehouse management
```

### Deployment Patterns

**Pattern 1: Local analytics script**
```python
# One-off analysis -- no server, no setup
import duckdb
duckdb.sql("""
    SELECT country, COUNT(*) as users
    FROM 's3://analytics/users_*.parquet'
    GROUP BY country
    ORDER BY users DESC
""").show()
```

**Pattern 2: ETL pipeline stage**
```python
# Read from multiple sources, transform, write output
con = duckdb.connect()
con.sql("""
    COPY (
        SELECT a.user_id, a.event, b.plan_type
        FROM read_parquet('events/*.parquet') a
        JOIN read_csv('users.csv') b ON a.user_id = b.id
        WHERE a.timestamp > '2025-01-01'
    ) TO 'output/enriched_events.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)
""")
```

**Pattern 3: Embedded in a web application**
```python
# FastAPI endpoint backed by DuckDB
from fastapi import FastAPI
import duckdb

app = FastAPI()
db = duckdb.connect('analytics.duckdb', read_only=True)

@app.get("/metrics/{metric}")
def get_metric(metric: str, days: int = 30):
    result = db.execute("""
        SELECT date, value FROM metrics
        WHERE metric_name = ? AND date > current_date - ?::INTEGER
        ORDER BY date
    """, [metric, days]).fetchdf()
    return result.to_dict(orient='records')
```

**Pattern 4: Data lakehouse with Iceberg**
```sql
INSTALL iceberg;
LOAD iceberg;

-- Query an Iceberg table on S3
SELECT * FROM iceberg_scan('s3://lakehouse/db/sales');

-- Time travel
SELECT * FROM iceberg_scan('s3://lakehouse/db/sales', version := '2');
```

---

## Use Cases & Case Studies
<!-- level: beginner-intermediate -->

### When to Use DuckDB

| Use Case | Why DuckDB Fits |
|----------|-----------------|
| **Ad-hoc data analysis** | SQL on local files with zero setup -- faster than pandas for large datasets |
| **ETL and data pipelines** | Read from multiple formats, transform with SQL, write to Parquet/CSV |
| **Data exploration** | Query CSVs, Parquet, JSON files directly without importing |
| **Embedded analytics** | Add analytical queries to applications without a separate database server |
| **CI/CD data testing** | Fast startup, no infrastructure -- ideal for testing data pipelines |
| **Privacy-sensitive analysis** | Data never leaves the local machine -- no cloud required |
| **Replacing pandas for SQL-heavy work** | Better memory efficiency, parallel execution, and SQL expressiveness |
| **Data lake querying** | Direct Parquet/Iceberg/S3 queries as a lightweight alternative to Spark |

### When NOT to Use DuckDB

| Scenario | Better Alternative |
|----------|--------------------|
| **High-concurrency OLTP** (many users writing simultaneously) | PostgreSQL, MySQL, CockroachDB |
| **Petabyte-scale distributed analytics** | ClickHouse, Snowflake, BigQuery, Spark |
| **Real-time streaming ingestion** | Kafka + ClickHouse, Apache Flink |
| **Multi-user concurrent writes** | PostgreSQL, any OLTP database |
| **Sub-millisecond point lookups** | Redis, DynamoDB, RocksDB |
| **Full-text search** | Elasticsearch, Typesense |

### Real-World Usage

**Watershed** -- Uses DuckDB for data pipeline operations, converting activity data into carbon footprint calculations. They query Parquet files directly as internal tooling.

**MotherDuck** -- A cloud service built on DuckDB that provides a serverless analytical database. Users can `ATTACH 'md:'` to offload heavy queries to cloud compute while keeping the DuckDB developer experience.

**Rill Data** -- Built their BI dashboard engine on DuckDB, powering interactive exploration of large datasets with sub-second query times.

**Evidence** -- Built Universal SQL with DuckDB-Wasm, enabling browser-based interactive dashboards that query data locally in WebAssembly.

**Common Production Pattern** -- Companies replace expensive cloud analytics services (BigQuery, Athena, Redshift) with DuckDB running in scheduled cloud functions (AWS Lambda, GCP Cloud Run), processing log files and Parquet directly from object storage at a fraction of the cost.

---

## Ecosystem & Integrations
<!-- level: intermediate -->

### Core Extensions (Maintained by DuckDB Team)

| Extension | Purpose |
|-----------|---------|
| **httpfs** | Read/write to S3, HTTP, HTTPS, and GCS |
| **parquet** | Parquet file reader/writer (bundled, auto-loaded) |
| **json** | JSON file reader (bundled, auto-loaded) |
| **iceberg** | Apache Iceberg table format (v2 and v3 support) |
| **spatial** | GIS/geometry functions; GEOMETRY type is core as of v1.5.0 |
| **postgres_scanner** | Directly query PostgreSQL tables |
| **sqlite_scanner** | Directly query SQLite databases |
| **excel** | Read/write Excel (.xlsx) files |
| **lance** | Lance lakehouse format (new in v1.5.1) |
| **ducklake** | Lakehouse catalog management |
| **fts** | Full-text search |
| **inet** | Network address types and functions |
| **tpch / tpcds** | Built-in benchmark data generators |

### Language Bindings

DuckDB provides official APIs for:
- **Python** (`pip install duckdb`) -- the most popular, with deep pandas/Polars integration
- **R** (`install.packages("duckdb")`) -- integrates with dplyr via dbplyr
- **Node.js** (`npm install duckdb`) -- async API for server-side JavaScript
- **Java/JDBC** -- standard JDBC driver
- **C/C++** -- native API, the foundation all other bindings build on
- **Go** -- community-maintained binding
- **Rust** -- via the `duckdb` crate
- **WebAssembly** -- DuckDB-Wasm runs entirely in the browser
- **ODBC** -- standard ODBC driver for legacy tool integration
- **Swift** -- for iOS/macOS applications

### Data Tool Integrations

| Tool | Integration |
|------|-------------|
| **dbt** | `dbt-duckdb` adapter for running dbt models locally |
| **Jupyter** | Magic commands via `duckdb` + `jupysql` |
| **Pandas** | Zero-copy querying of DataFrames with SQL |
| **Polars** | Query Polars DataFrames, export to Polars |
| **Apache Arrow** | Zero-copy data exchange via Arrow format |
| **Ibis** | DuckDB backend for the Ibis dataframe API |
| **Grafana** | DuckDB data source plugin for dashboards |
| **Airbyte** | DuckDB as a destination connector |
| **SQLAlchemy** | `duckdb_engine` dialect |
| **Metabase** | DuckDB driver for BI dashboards |

### MotherDuck (Cloud DuckDB)

MotherDuck provides a cloud-hosted DuckDB service:
- `ATTACH 'md:'` to connect your local DuckDB to the cloud
- Hybrid execution -- queries run locally or in the cloud depending on data location
- Shared databases for team collaboration
- Web-based SQL editor
- Cloud compute for heavy queries while keeping the local dev experience

---

## Common Q&A
<!-- level: all -->

### Q: How much data can DuckDB handle? When does it hit its limits?

DuckDB works well with datasets up to roughly **2 TB on a single machine**. The actual limit depends on your available RAM and disk:
- Datasets that fit in RAM: full speed, all operations in memory
- Datasets larger than RAM: DuckDB spills intermediate results to disk, so queries still work but slow down for operations that require materializing large intermediates (like big hash joins)
- Beyond ~2 TB or when you need distributed processing: consider ClickHouse, Snowflake, or Spark

The sweet spot is datasets from **1 MB to 200 GB** -- large enough that pandas struggles, small enough that you don't need a cluster.

### Q: Can I use DuckDB in production?

Yes, but understand its concurrency model. DuckDB supports **multiple concurrent readers but only a single writer**. This makes it well-suited for:
- Read-heavy analytical dashboards
- Batch processing pipelines
- Embedded analytics in applications
- Scheduled reporting jobs

It is **not suited** for workloads with many concurrent write transactions (use PostgreSQL or MySQL for that).

### Q: How does DuckDB compare to pandas for data analysis?

| Dimension | DuckDB | pandas |
|-----------|--------|--------|
| **Memory efficiency** | Columnar + spill to disk | Loads everything into RAM |
| **Query language** | SQL | Python API |
| **Parallelism** | Automatic multi-core | Single-threaded (mostly) |
| **Large datasets** | Handles larger-than-RAM | OOM on large data |
| **Complex joins** | Optimized by query planner | Manual, often slow |
| **Learning curve** | Need to know SQL | Need to know pandas API |

Many data professionals use both: DuckDB for heavy lifting (aggregations, joins, filtering), then convert results to pandas for visualization or ML.

### Q: What happens if my machine crashes mid-write? Is my data safe?

DuckDB is **ACID-compliant** with WAL (Write-Ahead Log) based recovery. If a crash occurs during a write:
- Uncommitted transactions are rolled back
- The database file remains consistent
- Committed data is never lost

The single-file format means there's no separate WAL directory to lose or corruption from partial file systems -- the WAL is embedded in the database file.

### Q: Can DuckDB replace my data warehouse (BigQuery/Snowflake)?

For many workloads, yes. Companies have replaced cloud data warehouses with DuckDB for:
- **Cost savings** -- DuckDB is free; cloud warehouses charge per query or per TB scanned
- **Latency** -- No network round-trip; queries on local data are faster
- **Simplicity** -- No infrastructure to manage

You'd still need a cloud warehouse when you require:
- Multiple teams querying the same data concurrently
- Petabyte-scale data
- Built-in governance, access control, and audit trails
- Real-time dashboard serving with high concurrency

### Q: How do I handle schema evolution with DuckDB?

DuckDB supports standard SQL DDL:
```sql
ALTER TABLE events ADD COLUMN source VARCHAR;
ALTER TABLE events DROP COLUMN old_field;
ALTER TABLE events RENAME COLUMN ts TO event_timestamp;
```

For file-based workflows (querying Parquet directly), schema evolution is handled by Parquet's built-in schema evolution -- DuckDB reads what columns exist and fills missing columns with NULL. For Iceberg tables, DuckDB respects Iceberg's schema evolution semantics (v2 and v3).

### Q: Is there a way to speed up repeated queries on the same data?

Several approaches:
1. **Persistent tables** -- Load data into a `.duckdb` file instead of querying raw files each time
2. **Indexes** -- Create ART (Adaptive Radix Tree) indexes for frequently filtered columns (use cautiously -- analytical workloads often don't benefit from indexes)
3. **Sorted data** -- Store data sorted by commonly filtered columns so zone maps can skip more row groups
4. **Parquet with row group statistics** -- Write Parquet files with sorted data so DuckDB's predicate pushdown is maximally effective

---

## Trade-offs & Limitations
<!-- level: intermediate -->

### Strengths

- **Zero-configuration deployment** -- No server, no dependencies, no configuration files. `pip install duckdb` and you're running queries.
- **Exceptional single-machine analytics performance** -- Vectorized columnar execution makes it remarkably fast for OLAP workloads, often matching or beating distributed systems on datasets that fit one machine.
- **Format versatility** -- Query Parquet, CSV, JSON, Iceberg, Lance, Excel, PostgreSQL, and SQLite data sources with a unified SQL interface.
- **Developer experience** -- The Python integration, DataFrame interop, and friendly CLI (v1.5.0+) make it pleasant to use for exploratory work.
- **Cost** -- MIT-licensed and free. Replacing cloud data warehouse queries with DuckDB can cut analytics costs dramatically.
- **Portability** -- Runs on Linux, macOS, Windows, in browsers (Wasm), mobile devices, and embedded systems. The same query runs everywhere.

### Limitations

- **Single-writer concurrency** -- Only one connection can write at a time. This is by design (not a bug), but it means DuckDB cannot serve high-concurrency write workloads. If you need many concurrent writers, use PostgreSQL or a distributed database.
- **Not distributed** -- DuckDB runs on a single machine. There's no built-in sharding, replication, or cluster mode. For datasets beyond ~2 TB, you'll need ClickHouse, Snowflake, Spark, or similar distributed systems.
- **Not an OLTP database** -- DuckDB is optimized for scans, aggregations, and joins -- not for high-throughput point lookups or single-row updates. Inserting millions of individual rows one-at-a-time is slow; bulk loading is the expected pattern.
- **Young ecosystem** -- While growing rapidly, the extension ecosystem is younger than PostgreSQL's. Some extensions are experimental, and breaking changes still occur between major versions (e.g., the `date_trunc` return type change in v1.5.0).
- **No built-in access control** -- DuckDB has no user management, roles, or row-level security. It trusts whoever has file access. For multi-tenant scenarios, you'd need to add access control at the application layer or use MotherDuck.
- **Storage format changes** -- DuckDB's on-disk format can change between major versions. While backward-compatible reads are supported and forward compatibility is maintained within LTS lines (e.g., 1.4.x), upgrading across major versions may require re-exporting data. The LTS release strategy (introduced with 1.4) mitigates this.

### Alternatives Comparison

| System | Best For | vs DuckDB |
|--------|----------|-----------|
| **SQLite** | OLTP, embedded transactional | DuckDB is 10-100x faster for analytics; SQLite wins for row-level inserts/updates |
| **ClickHouse** | Distributed real-time analytics | Better at petabyte scale and high concurrency; DuckDB is simpler and faster for single-machine work |
| **Polars** | DataFrame-centric analytics | More Pythonic API; DuckDB has richer SQL and can query more file formats |
| **Spark** | Distributed batch processing | Better at cluster-scale; DuckDB is orders of magnitude simpler and faster for single-machine data |
| **BigQuery/Snowflake** | Managed cloud analytics | Better governance, concurrency, and scale; DuckDB is free and faster for data that fits one machine |
| **PostgreSQL** | General-purpose with analytics | Better OLTP, access control, concurrency; DuckDB crushes it on analytical scans and aggregations |

### The Bottom Line

DuckDB excels when your data fits on one machine (up to ~2 TB) and your workload is analytical. It's the best choice for local data analysis, ETL pipelines, embedded analytics, and replacing expensive cloud queries. Choose something else when you need distributed scale, high write concurrency, or enterprise access control.
