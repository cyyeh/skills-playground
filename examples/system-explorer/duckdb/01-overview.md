## Overview

<!-- level: beginner -->

<!-- references:
- https://duckdb.org/why_duckdb
- https://duckdb.org/docs/stable/internals/overview
- https://github.com/duckdb/duckdb
- https://www.cidrdb.org/cidr2024/papers/p46-atwal.pdf
-->

### What Is DuckDB?

[DuckDB](https://duckdb.org) is an in-process analytical database management system (DBMS) designed for fast Online Analytical Processing ([OLAP](https://en.wikipedia.org/wiki/Online_analytical_processing)) workloads. It runs embedded inside your application -- no separate server process, no network configuration, no database administrator needed. You can think of it as **"SQLite for analytics"**: just as [SQLite](https://sqlite.org) made transactional databases effortlessly embeddable, DuckDB does the same for analytical queries over large datasets.

**One-sentence pitch:** DuckDB lets you run complex analytical SQL queries on gigabytes of data from CSV, Parquet, or JSON files directly from your Python script, R notebook, or command line -- with zero infrastructure setup and performance that rivals dedicated data warehouses.

### Real-World Analogy

Imagine you need to analyze sales data. The traditional approach is like renting a commercial kitchen (setting up a database server like PostgreSQL or deploying a cloud data warehouse) -- powerful but expensive and complex. SQLite is like a toaster oven -- great for small, simple meals (transactions) but struggles with a banquet (analytics). DuckDB is like a high-end home kitchen appliance -- it sits on your countertop (runs in your process), requires no installation crew (no server), and can handle a full dinner party (millions to billions of rows) with professional-grade performance.

### Who Is DuckDB For?

- **Data scientists and analysts** who want to query large local datasets with SQL without spinning up infrastructure
- **Data engineers** who need a fast, lightweight engine for ETL pipelines, data transformation, and testing
- **Application developers** who want to embed analytical query capabilities directly into their applications
- **Researchers** who need reproducible, portable data analysis without cloud dependencies
- **Anyone** who works with CSV, Parquet, JSON, or other data files and wants to use SQL on them immediately

### Key Characteristics

| Characteristic | Description |
|---|---|
| **In-Process** | Runs within your application process -- no client/server protocol overhead |
| **Columnar Storage** | Stores data by column rather than by row, optimized for analytical queries that touch few columns but many rows |
| **Vectorized Execution** | Processes data in batches of ~2048 values at a time, maximizing CPU cache efficiency |
| **Zero Dependencies** | Single binary or library with no external dependencies |
| **Feature-Rich SQL** | Supports window functions, CTEs, complex joins, nested types, and a rich set of SQL extensions |
| **Multi-Format Ingestion** | Reads CSV, Parquet, JSON, Arrow, Excel, and more -- directly, without importing first |
| **Free and Open Source** | MIT licensed, fully open source at [github.com/duckdb/duckdb](https://github.com/duckdb/duckdb) |
