## Trade-offs & Limitations

<!-- level: intermediate -->

<!-- references:
- https://duckdb.org/why_duckdb
- https://duckdb.org/docs/stable/connect/concurrency
- https://duckdb.org/2024/07/09/memory-management
- https://www.datacamp.com/blog/duckdb-vs-sqlite-complete-database-comparison
- https://motherduck.com/blog/duckdb-enterprise-5-key-categories/
-->

### Strengths

#### 1. Exceptional Single-Machine Analytical Performance
DuckDB's vectorized execution engine with morsel-driven parallelism delivers throughput that rivals or exceeds dedicated data warehouses for datasets that fit on a single machine. On the [ClickBench](https://benchmark.clickhouse.com/) analytical benchmark, DuckDB consistently ranks among the top performers in the single-machine category. For typical analytical queries on a 10 GB dataset, DuckDB completes in seconds what takes Pandas minutes and SQLite tens of seconds.

#### 2. Zero-Friction Setup
No server, no configuration files, no user management, no network setup. `pip install duckdb` and you are running analytical SQL in seconds. This eliminates the "ops tax" that prevents many teams from adopting analytical databases. A data scientist can go from raw CSV to insights in under a minute without any IT involvement.

#### 3. Multi-Format Data Access
DuckDB can query CSV, Parquet, JSON, Arrow, Excel, PostgreSQL, MySQL, SQLite, S3, HTTP URLs, and more -- often without any import step. This "query anything" capability eliminates the traditional ETL step of loading data into a database before you can query it.

#### 4. Deep Python/R Integration
Zero-copy data exchange with Pandas, Polars, and Arrow means DuckDB slots seamlessly into existing data science workflows. You can mix SQL and DataFrame operations in the same notebook without serialization overhead.

#### 5. Portable and Reproducible
A single `.duckdb` file contains the entire database -- schema, data, and indexes. Email it, commit it to git (for small databases), or share it via S3. No dump/restore, no schema migration scripts, no environment-specific configuration.

#### 6. Rich SQL Dialect
DuckDB's PostgreSQL-derived SQL dialect includes modern features that many analytical databases lack: `PIVOT`/`UNPIVOT`, `COLUMNS()` expressions, `SELECT * EXCLUDE`, `FROM`-first syntax, list comprehensions, recursive CTEs, and a growing set of aggregate and window functions. This makes complex analytical queries concise and readable.

### Limitations

#### 1. Single-Machine Only
DuckDB cannot distribute computation across a cluster. It is fundamentally a single-node system limited by that node's CPU, memory, and disk. For datasets or workloads that exceed a single machine's capacity (typically >100-200 GB working set), you need a distributed system like ClickHouse, BigQuery, or Snowflake.

#### 2. Single Writer Per Database File
Only one process can write to a DuckDB file at a time. This rules out architectures where multiple application instances write to a shared database. Within a single process, multiple threads can write concurrently, but multi-process write access is not supported and is unlikely to be supported in the future (by design, not by oversight).

#### 3. Not Designed for OLTP
DuckDB's columnar storage and vectorized execution are optimized for scanning many rows across few columns. Point lookups (fetch one row by primary key), frequent small updates, and high-concurrency transactional workloads are significantly slower than in row-oriented databases like PostgreSQL or SQLite. There are no B-tree indexes for range scans on individual rows.

#### 4. Larger-Than-Memory Limitations
While DuckDB supports spilling intermediate results to disk, this is a fallback mechanism, not a first-class feature. Not all operators support graceful degradation, performance drops significantly when spilling (10--100x slower for I/O-bound operations), and the temporary directory can consume large amounts of disk space. Datasets that routinely exceed available RAM are better served by systems designed for out-of-core processing.

#### 5. No Built-In Replication or High Availability
DuckDB provides no replication, failover, or backup mechanisms beyond the file system. For production deployments requiring high availability, you must implement backup strategies externally or use MotherDuck's managed service.

#### 6. Extension Security Model
Extensions run as native code in the same process with full system access. There is no sandboxing, capability system, or permission model for extensions. While core extensions are signed, community extensions require trust in their authors. This is acceptable for single-user analytical workflows but may concern security-sensitive deployments.

### Alternatives Comparison

#### DuckDB vs. SQLite

| Dimension | DuckDB | SQLite |
|-----------|--------|--------|
| **Workload** | OLAP (analytical queries) | OLTP (transactional operations) |
| **Storage** | Columnar | Row-oriented |
| **Execution** | Vectorized, parallel | Row-at-a-time, single-threaded |
| **Analytical query speed** | 8--100x faster on large scans | Slower for analytics, fast for point lookups |
| **Concurrency** | Single writer (per process), parallel readers | WAL mode allows concurrent reads + single writer |
| **Maturity** | Younger (first release 2019) | Very mature (20+ years) |
| **Ecosystem** | Growing rapidly | Massive, ubiquitous |
| **Best for** | Data analysis, ETL, embedded analytics | Mobile apps, config storage, small web apps |

**When to choose SQLite over DuckDB:** When your workload is primarily transactional (many small reads/writes), when you need the most battle-tested embedded database available, or when your data fits comfortably in a few hundred MB.

#### DuckDB vs. Polars

| Dimension | DuckDB | Polars |
|-----------|--------|--------|
| **Interface** | SQL-first | DataFrame-first (with SQL option) |
| **Language** | C++ core, multi-language bindings | Rust core, Python/R bindings |
| **Execution** | Vectorized SQL engine | Lazy DataFrame evaluation with query optimization |
| **Persistence** | Built-in single-file database | No built-in persistence (reads/writes files) |
| **SQL support** | Full-featured (window functions, CTEs, subqueries) | Basic SQL via `pl.sql()` |
| **Data sources** | 15+ formats, remote URLs, live databases | Parquet, CSV, JSON, Arrow |
| **Performance** | Comparable (within ~2x on most benchmarks) | Comparable (within ~2x on most benchmarks) |
| **Best for** | SQL-centric workflows, multi-format querying | Python-centric ETL, streaming transformations |

**When to choose Polars over DuckDB:** When your team prefers DataFrame operations over SQL, when you need streaming/lazy evaluation for memory-constrained ETL pipelines, or when you are building a pure Python data pipeline and want type-safe DataFrame operations.

#### DuckDB vs. ClickHouse

| Dimension | DuckDB | ClickHouse |
|-----------|--------|------------|
| **Architecture** | In-process, single-node | Client-server, single or multi-node |
| **Deployment** | Library/CLI, zero config | Server process, requires ops |
| **Concurrency** | Single writer, local readers | Many concurrent readers and writers |
| **Scale** | Single machine (~100 GB working set) | Petabyte-scale with clustering |
| **Ingestion** | Batch-oriented | High-throughput real-time ingestion |
| **SQL dialect** | PostgreSQL-compatible | ClickHouse SQL (some MySQL compatibility) |
| **Best for** | Local analytics, embedded use, data science | Production analytics, dashboards, monitoring |

**When to choose ClickHouse over DuckDB:** When you need a production analytics server with concurrent users, real-time data ingestion, cluster scaling, or when your dataset exceeds a single machine.

#### DuckDB vs. BigQuery / Snowflake

| Dimension | DuckDB | BigQuery / Snowflake |
|-----------|--------|---------------------|
| **Cost** | Free (MIT license) | Pay-per-query or pay-per-compute |
| **Scale** | Single machine | Virtually unlimited |
| **Setup** | Zero | Cloud account, IAM, networking |
| **Latency** | Milliseconds (in-process) | Seconds to minutes (cold start, compilation) |
| **Concurrency** | Single writer | Many concurrent users |
| **Data sharing** | File sharing | Built-in data sharing, marketplace |
| **Governance** | None built-in | Full RBAC, audit logs, compliance |
| **Best for** | Local analysis, prototyping, small teams | Enterprise analytics, data mesh, compliance |

**When to choose BigQuery/Snowflake over DuckDB:** When you need enterprise governance (RBAC, audit trails), multi-team collaboration, petabyte-scale storage, or when your organization already has cloud data infrastructure.

### Honest Take

DuckDB occupies a unique and valuable niche: it brings data warehouse-grade analytical performance to the individual developer's laptop, notebook, or application. Its closest analogy is SQLite -- not because they solve the same problem, but because they share the same philosophy of making powerful database technology effortlessly accessible.

**DuckDB is the right choice when** you are a single user or a small team analyzing datasets that fit on one machine (up to ~100-200 GB), and you value simplicity, speed, and zero operational overhead over distributed scaling and multi-user concurrency.

**DuckDB is the wrong choice when** you need a production database server with concurrent writers, real-time streaming ingestion, multi-node distribution, or enterprise access controls.

The most productive pattern for many organizations is using DuckDB and a cloud warehouse together: DuckDB for fast local development, testing, and ad-hoc exploration; the cloud warehouse for production workloads, multi-user access, and governance. Tools like MotherDuck, dbt-duckdb, and Ibis make this dual-use pattern practical by letting you develop locally with DuckDB and deploy to the cloud when ready.
