## Ecosystem & Integrations

<!-- level: intermediate -->

<!-- references:
- https://duckdb.org/docs/stable/extensions/overview
- https://motherduck.com/blog/duckdb-ecosystem-newsletter-december-2025/
- https://github.com/duckdb/dbt-duckdb
- https://motherduck.com
- https://duckdb.org/docs/stable/api/overview
-->

### Official Extensions

DuckDB ships with ~24 core extensions maintained by the DuckDB team. These are automatically installable via `INSTALL extension_name; LOAD extension_name;`:

| Extension | Purpose | Key Capability |
|-----------|---------|----------------|
| **parquet** | [Apache Parquet](https://parquet.apache.org/) support | Read/write Parquet files with predicate pushdown and column pruning |
| **json** | JSON processing | Query JSON files directly, JSON extraction functions, JSON type support |
| **httpfs** | Remote file access | Read files from HTTP/HTTPS URLs, S3, GCS, and Azure Blob Storage |
| **icu** | Unicode collation | Locale-aware string comparison, timezone support via [ICU library](https://icu.unicode.org/) |
| **spatial** | Geospatial operations | ST_Point, ST_Distance, R-tree indexes, GeoJSON/WKT support (58x faster spatial joins via R-tree in 2025) |
| **postgres_scanner** | PostgreSQL integration | Query live PostgreSQL databases directly from DuckDB |
| **mysql_scanner** | MySQL integration | Query live MySQL databases directly from DuckDB |
| **sqlite_scanner** | SQLite integration | Query SQLite database files directly |
| **excel** | Excel file support | Read `.xlsx` files as tables |
| **fts** | Full-text search | Create full-text indexes and perform text search queries |
| **tpch** / **tpcds** | Benchmarking | Generate TPC-H and TPC-DS benchmark data for performance testing |
| **iceberg** | Apache Iceberg support | Read and write [Apache Iceberg](https://iceberg.apache.org/) tables, including metadata management |
| **delta** | Delta Lake support | Read [Delta Lake](https://delta.io/) tables |
| **aws** | AWS credential management | Automatic AWS credential chain resolution for S3 access |
| **azure** | Azure integration | Azure Blob Storage access and credential management |
| **inet** | Network types | IP address and CIDR types with operations |
| **autocomplete** | SQL autocompletion | Tab completion support for the CLI |
| **jemalloc** | Memory allocator | Use [jemalloc](https://jemalloc.net/) for improved memory allocation performance on Linux |
| **substrait** | Query plan exchange | Import/export query plans in [Substrait](https://substrait.io/) format |
| **vss** | Vector similarity search | HNSW indexes for approximate nearest neighbor search |

### Community Extensions

As of late 2025, the DuckDB community has built over 100 extensions. Notable community extensions include:

| Extension | Author/Project | Purpose |
|-----------|----------------|---------|
| **quackstore** | Community | Block-based caching for remote files (1 MB blocks with LRU eviction) |
| **osmextract** | Community | Extract OpenStreetMap PBF data into GeoParquet using DuckDB spatial |
| **lance** | LanceDB | Read [Lance](https://lancedb.com/) columnar format for ML data |
| **chsql** | Community | ClickHouse-compatible SQL syntax |
| **prql** | PRQL | [PRQL](https://prql-lang.org/) language support as an alternative to SQL |
| **scrooge** | Community | Financial data types and functions |
| **crypto** | Community | Cryptographic hash functions (SHA-256, etc.) |

Extensions can be authored in C++, Rust, Python, or even Shell scripts, demonstrating the flexibility of DuckDB's extension API.

### Key Ecosystem Tools

#### MotherDuck -- Cloud-Native DuckDB

[MotherDuck](https://motherduck.com) is the commercial cloud service built around DuckDB. It provides:

- **Hybrid execution:** Queries can execute partially on local DuckDB and partially in the cloud, with data automatically routed to the optimal location
- **Shared databases:** Multiple users can access the same datasets with proper access control
- **Persistent cloud storage:** Data stored durably in the cloud, accessible from any DuckDB client
- **Collaboration:** Share queries, results, and databases with team members
- **MotherDuck token authentication:** Simple `md:` connection string prefix for seamless integration

```python
import duckdb
# Connect to MotherDuck cloud
con = duckdb.connect("md:my_database?motherduck_token=<token>")
con.sql("SELECT * FROM cloud_table LIMIT 10").show()
```

#### dbt-duckdb -- Data Build Tool Integration

[dbt-duckdb](https://github.com/duckdb/dbt-duckdb) is the official [dbt](https://www.getdbt.com/) adapter for DuckDB. It enables:

- Running dbt models against local DuckDB databases or MotherDuck
- Full dbt feature support: models, tests, snapshots, seeds, documentation
- CI/CD pipeline testing without a cloud warehouse
- Local development with instant feedback (no waiting for cloud query compilation)

```yaml
# profiles.yml for dbt-duckdb
my_project:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: 'dev.duckdb'
      threads: 4
    prod:
      type: duckdb
      path: 'md:my_production_db'  # MotherDuck
```

#### Evidence.dev -- BI as Code

[Evidence](https://evidence.dev) is a code-first business intelligence tool that uses DuckDB as its local query engine. Analysts write SQL in Markdown files, and Evidence renders them as interactive dashboards. DuckDB's speed makes the development feedback loop nearly instant.

#### pg_duckdb -- OLAP Analytics in PostgreSQL

[pg_duckdb](https://github.com/duckdb/pg_duckdb) embeds DuckDB inside PostgreSQL as an extension. When PostgreSQL detects an analytical query, it can route it to DuckDB's execution engine for dramatically faster performance while keeping transactional queries on PostgreSQL's engine. Version 1.0 released in 2025.

#### Ibis -- Universal DataFrame API

[Ibis](https://ibis-project.org) provides a Python DataFrame API that can target multiple backends, including DuckDB. Users write Ibis expressions, and the framework compiles them to DuckDB SQL for local execution or to other backends (BigQuery, Snowflake, Spark) for remote execution.

### Language Client Libraries

DuckDB provides official client libraries for many languages:

| Language | Package | Notes |
|----------|---------|-------|
| **Python** | `pip install duckdb` | Most popular. Zero-copy integration with Pandas, Polars, Arrow |
| **R** | `install.packages("duckdb")` | DBI-compatible interface, works with dbplyr and dplyr |
| **Node.js** | `npm install duckdb` | Native bindings, async API |
| **Java/Kotlin** | JDBC driver | Standard JDBC interface for JVM applications |
| **Rust** | `cargo add duckdb` | Native Rust bindings with Arrow integration |
| **Go** | `go-duckdb` | CGo-based bindings |
| **C/C++** | Header-only or shared library | Core API, most direct access |
| **Swift** | Swift package | macOS and iOS support |
| **C#/.NET** | NuGet package | ADO.NET compatible provider |
| **WebAssembly** | `@duckdb/duckdb-wasm` | Run DuckDB in the browser via WASM |
| **CLI** | Binary download | Interactive SQL shell with auto-completion |

### Integration Patterns

#### Pattern 1: DuckDB as a Local Analytics Cache

```
Cloud Data Warehouse (BigQuery/Snowflake)
           |
           | Export to Parquet (nightly)
           v
     Local Parquet Files
           |
           | Query via DuckDB
           v
   Application / Dashboard
```

Use DuckDB to query exported snapshots locally, reducing cloud costs and latency for frequently-accessed data.

#### Pattern 2: DuckDB as an ETL Engine

```
Raw Data Sources (CSV, JSON, APIs)
           |
           | DuckDB SQL transformations
           v
   Cleaned Parquet / Iceberg Tables
           |
           | Upload to cloud or serve locally
           v
   Data Warehouse or Data Lake
```

Use DuckDB to clean, transform, and aggregate raw data before loading into production systems.

#### Pattern 3: DuckDB in the Browser

```
Static Parquet Files (hosted on CDN)
           |
           | Fetched by duckdb-wasm
           v
   Browser-based DuckDB (WASM)
           |
           | Interactive SQL queries
           v
   Client-side Dashboard (React/Vue)
```

Use duckdb-wasm to build serverless analytics dashboards where all computation happens in the user's browser.
