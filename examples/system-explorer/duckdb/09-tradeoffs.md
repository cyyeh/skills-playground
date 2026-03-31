## Trade-offs & Limitations
<!-- level: intermediate -->
<!-- references:
- [DuckDB vs SQLite: Performance Comparison](https://www.analyticsvidhya.com/blog/2026/01/duckdb-vs-sqlite/) | blog
- [Polars Updated PDS-H Benchmark Results](https://pola.rs/posts/benchmarks/) | blog
- [Should You Ditch Spark for DuckDB or Polars?](https://milescole.dev/data-engineering/2024/12/12/Should-You-Ditch-Spark-DuckDB-Polars.html) | blog
-->

### Strengths

**Zero-friction deployment.** No server, no configuration, no dependencies. `pip install duckdb` and you're running queries in seconds. This is DuckDB's killer feature — it removes the entire "set up infrastructure" step from analytical work. You can share a `.duckdb` file like you'd share a spreadsheet.

**Best-in-class single-node analytical performance.** DuckDB's combination of columnar storage, vectorized execution, and morsel-driven parallelism delivers performance that competes with dedicated analytical databases on single-machine workloads. On TPC-H SF10, DuckDB matches or outperforms Hyper and is within striking distance of ClickHouse — while running as an embedded library.

**Universal data access.** DuckDB reads Parquet, CSV, JSON, Excel, Arrow, and IPC files directly. It queries pandas DataFrames, Polars LazyFrames, and Arrow tables with zero copy. It connects to PostgreSQL, MySQL, SQLite, SQL Server, and MongoDB. It reads from S3, GCS, Azure, and HTTP. No other embedded database comes close to this breadth of data access.

**SQL completeness.** DuckDB supports a remarkably complete SQL dialect — window functions, CTEs, recursive queries, LATERAL joins, GROUPING SETS, QUALIFY, PIVOT/UNPIVOT, list/struct/map types, lambda functions, and the new VARIANT type. For SQL-first analysts, DuckDB is the most capable embedded option available.

**Active development and community.** With monthly releases, 127+ community extensions, and commercial backing from MotherDuck, DuckDB has one of the most active development communities in the database space. The extension system makes it straightforward to add new functionality without forking the core.

### Limitations

**Single-writer concurrency.** Only one process can write to a DuckDB database at a time. Multiple concurrent writers require external coordination or switching to a client-server database. This is a fundamental limitation of the embedded architecture — there's no server process to arbitrate write access.

**No OLTP optimization.** DuckDB has no B-tree indexes for point lookups. Single-row retrieval is ~4× slower than SQLite. If your workload mixes analytical queries with frequent single-record reads/writes (e.g., serving a web application), DuckDB is the wrong tool.

**Single-machine scale ceiling.** DuckDB runs on one machine. While it handles 100GB+ datasets, truly massive workloads (multi-TB) need distributed processing. MotherDuck extends DuckDB to the cloud, but for native multi-node parallelism, alternatives like Spark or ClickHouse are more appropriate.

**Storage format evolution.** DuckDB's storage format has changed between major versions, requiring export/import cycles during upgrades. The introduction of the v1.4.x LTS line mitigates this, but organizations running DuckDB in production need to plan for storage format migrations.

**Limited real-time ingestion.** DuckDB is batch-oriented. It doesn't support streaming ingestion, change data capture, or real-time materialized views. For use cases requiring sub-second data freshness, pair DuckDB with a streaming system or use a database designed for real-time workloads.

### Alternatives Comparison

**SQLite** — The incumbent embedded database. SQLite is unbeatable for OLTP: point lookups, single-record inserts, transactional mobile apps. Choose SQLite when your workload is transactional (many small reads/writes) rather than analytical (few large scans/aggregations). DuckDB is 8–50× faster for analytical queries; SQLite is 4× faster for point lookups. They can coexist — DuckDB can query SQLite databases directly via the `sqlite_scanner` extension.

**Polars** — A DataFrame library for Python and Rust. Polars and DuckDB are close in performance for analytical operations, with DuckDB generally winning on complex SQL queries and Polars excelling in programmatic DataFrame pipelines. Choose Polars when: you prefer a DataFrame API over SQL, your pipeline is Python-native, or you need lazy evaluation with query plan optimization. Choose DuckDB when: you prefer SQL, need to query files/databases directly, or want a persistent database with transactions. For 10GB workloads, DuckDB is ~2× faster than Polars; at 100GB, they're closer.

**Apache Spark** — The standard for distributed data processing. Choose Spark when your data exceeds what one machine can handle, when you need a mature ecosystem of ML libraries (MLlib), or when you're already running on a Spark cluster. DuckDB is orders of magnitude simpler to deploy and faster on single-machine workloads. Atlan is replacing Apache Spark with DuckDB for workloads that fit on one machine — a trend in the industry. For datasets under 100GB, DuckDB + a single machine is almost always cheaper and faster than a Spark cluster.

### The Honest Take

DuckDB is the right choice when you need analytical query power without infrastructure overhead. It's the best tool for data scientists who want SQL on local files, data engineers building pipelines on datasets under 100GB, and application developers embedding analytics in their products. It's not the right choice for multi-user transactional applications, multi-terabyte distributed workloads, or real-time streaming analytics. The "SQLite for analytics" positioning is accurate — just as you wouldn't build a high-concurrency web backend on SQLite, you wouldn't build a petabyte-scale data warehouse on DuckDB. Within its niche, it's exceptional.
