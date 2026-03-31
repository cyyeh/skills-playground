## Overview
<!-- level: beginner -->
<!-- references:
- [DuckDB Official Documentation](https://duckdb.org/docs/) | official-docs
- [DuckDB: An In-Process OLAP Database (SIGMOD 2019)](https://ir.cwi.nl/pub/28549) | paper
- [What Is DuckDB? Introduction, Use Cases & Architecture](https://motherduck.com/duckdb-book-summary-chapter1/) | blog
-->

DuckDB is an in-process analytical database management system designed to make running complex analytical queries on local data as simple as importing a library. Think of it as "SQLite for analytics" — where SQLite excels at transactional workloads (reading and writing individual records), DuckDB is purpose-built for analytical workloads (scanning and aggregating large volumes of data).

Created at [CWI Amsterdam](https://www.cwi.nl/) by Mark Raasveldt and Hannes Mühleisen, DuckDB was born from the frustration of researchers who needed to run analytical queries on datasets without the overhead of setting up and maintaining a database server. The result is a database that runs inside your application's process — no server, no configuration, no dependencies — yet delivers performance that rivals dedicated analytical database servers.

### What It Is

DuckDB is an embedded columnar database engine — like having a personal data warehouse that lives inside your Python script, R session, or application binary. You `pip install duckdb`, write a SQL query against a Parquet file, and get results in seconds — no server, no ETL pipeline, no cloud account required.

### Who It's For

DuckDB is built for data analysts, data scientists, and data engineers who work with datasets ranging from megabytes to hundreds of gigabytes. It's ideal for anyone who currently loads CSV files into pandas, runs SQL against SQLite for analytics, or spins up a database server just to crunch numbers. It's also increasingly used in production for embedded analytics, data pipelines, and browser-based data applications via WebAssembly.

### The One-Sentence Pitch

DuckDB gives you the analytical power of a columnar data warehouse in a zero-dependency embeddable library that runs anywhere — from a Jupyter notebook to a web browser.
