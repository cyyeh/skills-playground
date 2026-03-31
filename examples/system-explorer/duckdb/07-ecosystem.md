## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [DuckDB Community Extensions](https://duckdb.org/2024/07/05/community-extensions) | official-docs
- [DuckDB Ecosystem Newsletter — March 2026](https://motherduck.com/blog/duckdb-ecosystem-newsletter-march-2026/) | community
- [MotherDuck: DuckDB in the Cloud](https://motherduck.com/) | official-docs
-->

### Official Tools & Extensions

**Core Extensions (bundled or auto-installable):**
- **`httpfs`** — Read/write files from HTTP, S3, GCS, and Azure Blob Storage. Enables `SELECT * FROM read_parquet('s3://bucket/data.parquet')` directly.
- **`json`** — Native JSON reading with automatic schema inference. Handles JSONL, nested JSON, and mixed-type arrays.
- **`parquet`** — Advanced Parquet support including predicate pushdown, column pruning, and partitioned writes.
- **`postgres_scanner`** — Attach and query PostgreSQL databases directly from DuckDB. Supports filter pushdown to the remote server.
- **`mysql_scanner`** — Same as above for MySQL databases.
- **`sqlite_scanner`** — Attach SQLite databases and query them via DuckDB's analytical engine.
- **`spatial`** — Geospatial functions (ST_Distance, ST_Contains, etc.) with the new built-in GEOMETRY type (v1.5.0+).
- **`iceberg`** — Read Apache Iceberg tables, enabling DuckDB as a lakehouse query engine.
- **`delta`** — Read Delta Lake tables with full support for time travel and schema evolution.
- **`fts`** — Full-text search with BM25 scoring, enabling `WHERE fts_match(content, 'search query')`.
- **`excel`** — Read and write Excel files (.xlsx).

**DuckDB CLI (v1.5.0+):** The command-line client received a major overhaul with syntax highlighting, dynamic prompts showing current database/schema, a built-in pager, the `_` operator to reference previous results, and `.tables` / `DESCRIBE` for schema exploration.

**DuckDB WASM:** The full DuckDB engine compiled to WebAssembly for browser environments. Powers interactive data applications, notebook environments, and serverless analytics.

### Community Ecosystem

With [127+ community extensions](https://duckdb.org/community_extensions/development), DuckDB's ecosystem is growing rapidly:

- **`mssql`** — Native TDS protocol communication with Microsoft SQL Server (zero dependencies, TLS/SSL, connection pooling)
- **`snowflake`** — Query Snowflake tables directly from DuckDB via ADBC
- **`mongo`** — SQL queries against MongoDB collections with automatic schema inference and filter pushdown
- **`infera`** — Run ONNX ML models inside SQL queries
- **`onager`** — Graph analytics (centrality, community detection) implemented in Rust
- **`dns`** — DNS lookup and reverse DNS as SQL functions
- **`gaggle`** — Query Kaggle datasets directly via SQL

**ExtensionKit (.NET):** [DuckDB.ExtensionKit](https://duckdb.org/2026/03/20/duckdb-extensionkit-csharp) enables building DuckDB extensions in C# using .NET Native AOT compilation, broadening the extension developer community beyond C/C++.

### Common Integration Patterns

**DuckDB + dbt:** Use dbt-duckdb to run dbt transformations locally with DuckDB. Ideal for development and testing of data models before deploying to a production warehouse. The NSW Department of Education uses this pattern for their data portal.

**DuckDB + Pandas/Polars:** DuckDB queries pandas DataFrames and Polars LazyFrames directly without copying data (via Apache Arrow). Use DuckDB for complex SQL operations, then hand results back to Python for visualization or ML.

```python
import duckdb, pandas as pd
df = pd.read_csv('large_file.csv')
result = duckdb.sql("SELECT category, AVG(value) FROM df GROUP BY category").fetchdf()
```

**DuckDB + MotherDuck (Cloud):** [MotherDuck](https://motherduck.com/) extends DuckDB to the cloud with hybrid query processing — queries execute partly on the client and partly in the cloud, with the optimizer choosing the most efficient split. Databases are shared via URLs, enabling collaboration without data export/import.

**DuckDB + Lakehouse (Iceberg/Delta):** Use DuckDB as a lightweight query engine for data lakehouses. Read Iceberg or Delta tables from S3/GCS, benefiting from DuckDB's vectorized execution without spinning up Spark clusters. Effective for ad-hoc exploration of lakehouse data.

**DuckDB + Evidence/Rill/Hex (BI tools):** Multiple business intelligence tools embed DuckDB as their analytical engine. Evidence uses it as a universal SQL backend, Rill powers interactive dashboards, and Hex accelerates notebook analytics. The pattern is consistent: embed DuckDB for fast, local-first analytics with optional cloud scaling via MotherDuck.

**DuckDB + Arrow Flight:** Share DuckDB query results across processes or languages using Apache Arrow Flight. DuckDB's native Arrow support means zero-copy data exchange with any Arrow-compatible tool.
