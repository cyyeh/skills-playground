## Use Cases & Case Studies

<!-- level: beginner-intermediate -->

<!-- references:
- https://motherduck.com/blog/15-companies-duckdb-in-prod/
- https://duckdb.org/why_duckdb
- https://shekhargulati.com/2024/08/04/how-developers-utilize-duckdb-use-cases-and-suitability/
- https://motherduck.com/blog/duckdb-enterprise-5-key-categories/
- https://www.robinlinacre.com/recommend_duckdb/
-->

### When to Use DuckDB

#### 1. Local Data Exploration and Ad-Hoc Analysis

**Scenario:** You have a collection of CSV, Parquet, or JSON files and need to quickly answer questions about the data without setting up infrastructure.

**Why DuckDB excels:** Zero setup time. You can query files directly without importing them. DuckDB auto-detects schemas, handles type inference, and processes gigabytes of data in seconds on a laptop.

```python
# Explore a 5 GB dataset in seconds -- no database setup needed
import duckdb
duckdb.sql("""
    FROM 'sales_data/*.parquet'
    SELECT product_category, 
           SUM(revenue) as total,
           COUNT(*) as transactions
    GROUP BY product_category
    ORDER BY total DESC
    LIMIT 20
""").show()
```

**Real-world example:** Data journalists at news organizations use DuckDB to explore public datasets (government spending, election data, census records) directly from downloaded files, enabling rapid investigation without IT support.

#### 2. Data Science and Machine Learning Pipelines

**Scenario:** A data scientist needs to prepare features from multiple data sources, perform complex aggregations, and feed results into a ML model.

**Why DuckDB excels:** Native integration with Python data science tools (Pandas, Polars, Arrow). Zero-copy data transfer means no serialization overhead. SQL is often more expressive than DataFrame operations for complex joins and window functions.

**Real-world example:** [Hex](https://hex.tech) integrated DuckDB into their collaborative notebook platform and achieved 5--10x speedups in notebook execution for data transformation steps. Users write SQL cells that execute locally via DuckDB rather than round-tripping to a remote data warehouse.

#### 3. ETL and Data Transformation

**Scenario:** A data engineering team needs to transform raw data files into cleaned, aggregated datasets for downstream consumption.

**Why DuckDB excels:** DuckDB can read from and write to multiple formats (CSV, Parquet, JSON, Arrow, Iceberg) directly. Its parallel execution engine processes transformations faster than Pandas/Spark for medium-sized datasets (up to tens of GB). No cluster infrastructure needed.

**Real-world example:** [FinQore](https://motherduck.com/blog/15-companies-duckdb-in-prod/) replaced their Spark-based ETL pipeline with DuckDB and reduced processing time from 8 hours to 8 minutes for their financial data transformations. The simpler architecture (single binary vs. Spark cluster) also reduced operational overhead significantly.

#### 4. Embedded Analytics in Applications

**Scenario:** A SaaS application needs to provide analytics dashboards, reports, or data exploration features to users without adding a separate database server.

**Why DuckDB excels:** As an in-process library, DuckDB can be embedded directly into web servers, desktop applications, or CLI tools. Users get analytical query performance without the complexity of a separate analytics database.

**Real-world example:** The government of South Australia uses [duckdb-wasm](https://duckdb.org/docs/api/wasm/overview) (DuckDB compiled to WebAssembly) in their climate change dashboard. The entire analytical database runs in the user's browser, enabling interactive data exploration without server-side query processing.

#### 5. CI/CD and Data Pipeline Testing

**Scenario:** A data engineering team needs to test their dbt models, SQL transformations, or data quality checks in CI without provisioning a database.

**Why DuckDB excels:** Near-zero startup time (milliseconds), no server process to manage, and full SQL compatibility. Tests can create an in-memory database, load test fixtures, run transformations, and verify results -- all in a single process.

**Real-world example:** Teams using [dbt-duckdb](https://github.com/duckdb/dbt-duckdb) run their entire dbt test suite against DuckDB in CI/CD pipelines, avoiding the cost and complexity of maintaining a test warehouse (Snowflake, BigQuery, Redshift).

#### 6. Edge and IoT Analytics

**Scenario:** Analytical processing needed on edge devices, IoT gateways, or environments with limited resources and no network connectivity.

**Why DuckDB excels:** Small binary size (~25 MB), no external dependencies, efficient memory usage. Can run meaningful analytical queries on devices with as little as 256 MB of RAM.

**Real-world example:** Industrial monitoring systems use embedded DuckDB to aggregate sensor data locally on edge devices, computing rolling averages, anomaly detection thresholds, and summary statistics without sending raw data to the cloud.

### When NOT to Use DuckDB

#### High-Concurrency OLTP Workloads

**Scenario:** A web application serving thousands of concurrent users with frequent small INSERT/UPDATE/DELETE operations.

**Why DuckDB is wrong:** DuckDB is optimized for analytical workloads (scanning many rows, aggregating columns) not transactional workloads (many small random reads/writes). It supports only a single writer process and uses columnar storage that is inefficient for single-row operations. Use PostgreSQL, MySQL, or SQLite instead.

#### Multi-User Server Database

**Scenario:** Multiple applications or users need to connect to a shared database simultaneously, with concurrent reads and writes.

**Why DuckDB is wrong:** DuckDB's in-process architecture means each process gets its own instance. Concurrent write access from multiple processes to the same database file is not supported. For multi-user scenarios, use PostgreSQL, ClickHouse, or consider [MotherDuck](https://motherduck.com) (DuckDB as a cloud service with multi-tenant support).

#### Very High-Volume Streaming Data

**Scenario:** Ingesting millions of events per second in real-time with low-latency query requirements.

**Why DuckDB is wrong:** DuckDB is designed for batch analytical processing, not real-time streaming. It lacks features like continuous queries, change data capture, or streaming ingestion. Use Apache Kafka + ClickHouse, Apache Flink, or Materialize instead.

#### Petabyte-Scale Data Warehousing

**Scenario:** Querying petabytes of data distributed across hundreds of machines.

**Why DuckDB is wrong:** DuckDB runs on a single machine and is limited by that machine's resources. While it handles datasets larger than memory via spilling to disk, it cannot distribute computation across a cluster. For petabyte-scale warehousing, use BigQuery, Snowflake, Redshift, or ClickHouse clusters.

### Production Deployment Highlights

| Company | Use Case | Result |
|---------|----------|--------|
| **Watershed** | Carbon emissions analytics | 10x performance gain with zero-copy SQL queries |
| **FinQore** | Financial data ETL | Reduced pipeline from 8 hours to 8 minutes |
| **Okta** | Security event processing | Processed 7.5 trillion security records |
| **Hex** | Notebook execution engine | 5--10x speedup in data transformation steps |
| **GoodData** | Concurrent analytics dashboards | Superior concurrent user performance |
| **South Australia Gov** | Climate change dashboard | Browser-based analytics via DuckDB-WASM |
| **dbt Labs** | Data transformation testing | CI/CD pipeline testing without warehouse costs |
