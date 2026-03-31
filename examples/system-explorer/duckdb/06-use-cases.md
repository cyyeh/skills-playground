## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
<!-- references:
- [15+ Companies Using DuckDB in Production](https://motherduck.com/blog/15-companies-duckdb-in-prod/) | blog
- [The Enterprise Case for DuckDB](https://motherduck.com/blog/duckdb-enterprise-5-key-categories/) | blog
- [DuckDB in Practice: Enterprise Integration Patterns](https://endjin.com/blog/2025/04/duckdb-in-practice-enterprise-integration-architectural-patterns) | blog
-->

### When to Use It

**Ad-hoc analytical queries on local files.** You have Parquet, CSV, or JSON files and need answers fast. DuckDB queries these directly without a loading step — `SELECT AVG(price) FROM 'sales.parquet' WHERE region = 'EMEA'` just works. This is DuckDB's sweet spot: data scientist with a laptop and a question.

**Data pipeline transformations (ETL/ELT).** Replace pandas or Spark for small-to-medium data transformations (up to ~100GB). DuckDB's SQL engine is faster and more memory-efficient than pandas for aggregations and joins. FinQore (formerly SaaSWorks) cut their financial ETL pipeline from 8 hours to 8 minutes by replacing PostgreSQL with DuckDB.

**Embedded analytics in applications.** Ship DuckDB inside your product to provide analytical query capabilities without requiring users to set up a database server. Evidence uses DuckDB as a universal SQL engine for business intelligence, and Rill uses it as the backbone of their visual analytics platform (3×–30× faster than SQLite for analytical queries).

**Interactive data exploration in notebooks.** In Jupyter, R, or Observable notebooks, DuckDB provides instant SQL querying of DataFrames, Arrow tables, and files. Hex reports 5–10× speedups in notebook execution after switching to DuckDB.

**Browser-based analytics.** DuckDB compiles to WebAssembly, enabling analytical queries directly in web browsers. The government of South Australia uses duckdb-wasm for their [climate change data dashboard](https://www.data.sa.gov.au/). Mosaic used it to explore 18M data points from the Gaia star catalog entirely in-browser.

### When NOT to Use It

**High-concurrency OLTP workloads.** DuckDB is not a replacement for PostgreSQL, MySQL, or SQLite for transaction-heavy applications with hundreds of concurrent users doing point reads and writes. It supports one writer at a time and is optimized for scanning, not key-value lookups.

**Multi-terabyte distributed datasets.** DuckDB runs on a single machine. If your data exceeds what one machine can handle (typically beyond ~500GB–1TB), use distributed systems like Apache Spark, ClickHouse, or BigQuery. MotherDuck extends DuckDB to the cloud with hybrid execution, but for truly massive datasets, native distributed systems are more appropriate.

**Real-time streaming ingestion.** DuckDB is designed for batch-oriented analytical queries, not continuous streaming. For real-time event processing, use Kafka + Flink or similar streaming architectures. DuckDB works well for querying the results of streaming pipelines after they land in Parquet files.

**Multi-user shared database.** DuckDB is an embedded database — it's designed for single-user or single-application access. If multiple services need to share a database with concurrent read-write access, use a client-server database like PostgreSQL.

### Real-World Examples

**Watershed — Carbon Analytics (750MB, 75K queries/day)**
Watershed processes carbon footprint data for enterprises. They store customer datasets as Parquet files on Google Cloud Storage (largest: ~750MB, 17M rows) and use DuckDB to translate natural-language analytics requests into SQL. DuckDB delivers 10× faster performance versus their previous PostgreSQL setup, handling 75,000 daily queries.

**Okta — Enterprise Security (7.5 Trillion Records)**
Okta, a Fortune 500 identity provider, uses DuckDB to process security telemetry at massive scale — 7.5 trillion records. DuckDB's ability to efficiently scan and aggregate columnar data makes it viable for security analytics workloads that would traditionally require dedicated distributed infrastructure.

**Hugging Face — AI Dataset Access (150K+ Datasets)**
Hugging Face integrated DuckDB to provide SQL querying across their 150,000+ AI/ML datasets. Users query datasets directly using `hf://` protocol URLs, making it trivial to explore and filter training data without downloading entire datasets.

**NSW Department of Education — Data Portal**
Australia's NSW Department of Education uses DuckDB as part of a modern data stack (Dagster + dbt + dlt + Evidence) for their education data portal. DuckDB enables local-first development and testing of analytical pipelines before deploying to production.

**Ibis Project — 1.1B Rows in 38 Seconds**
The Ibis team processed 1.1 billion PyPI package download rows in 38 seconds on a laptop using only 1GB of RAM, demonstrating DuckDB's efficiency for large-scale analytical processing on commodity hardware.
