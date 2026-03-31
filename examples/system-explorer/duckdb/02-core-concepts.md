## Core Concepts

<!-- level: beginner -->

<!-- references:
- https://duckdb.org/docs/stable/internals/vector
- https://duckdb.org/docs/stable/internals/overview
- https://duckdb.org/why_duckdb
- https://duckdb.org/docs/stable/extensions/overview
- https://endjin.com/blog/2025/04/duckdb-in-depth-how-it-works-what-makes-it-fast
-->

### 1. Columnar Storage

[Columnar storage](https://en.wikipedia.org/wiki/Column-oriented_DBMS) means data is organized by column rather than by row. When a query asks "what is the average salary?", DuckDB reads only the salary column and skips everything else.

**Analogy:** Think of a library. A row-based database is like a library where each book contains one person's entire life story -- to find everyone's birthday, you'd need to open every single book. A columnar database is like having separate filing cabinets for "birthdays," "addresses," and "names" -- to find all birthdays, you open just one cabinet and scan through it. This is dramatically faster when you only need a few fields from millions of records.

**Why it matters:** Analytical queries typically scan many rows but only a few columns (e.g., `SELECT AVG(price) FROM sales`). Columnar layout means DuckDB reads orders of magnitude less data from disk and memory, and the contiguous column data compresses extremely well.

### 2. Vectorized Execution

[Vectorized execution](https://duckdb.org/docs/stable/internals/vector) processes data in batches (called "vectors") of up to 2048 values at a time, rather than one row at a time. Each operator in the query plan works on an entire vector before passing results to the next operator.

**Analogy:** Imagine a factory assembly line. Row-at-a-time processing is like a worker picking up one widget, carrying it through every station, and then going back for the next one. Vectorized execution is like loading a tray of 2048 widgets and running the entire tray through each station at once. The tray is sized to fit perfectly on the workbench (CPU L1 cache), so the worker never has to leave their station to fetch parts.

**Why it matters:** Vectorized processing keeps data in CPU caches (the L1 cache is typically 32--128 KB), reduces per-row function call overhead by ~2000x, and enables the compiler to automatically generate [SIMD](https://en.wikipedia.org/wiki/SIMD) instructions that process multiple values in a single CPU cycle.

### 3. In-Process Architecture

DuckDB runs as a library embedded directly in your application process. There is no separate database server, no network communication, and no client-server protocol. You link DuckDB into your Python, R, Java, or C++ program and call it like a function.

**Analogy:** Traditional database servers are like a restaurant -- you (the client) sit at a table, send orders (queries) to the kitchen (server) over a waiter (network), and wait for food (results) to come back. DuckDB is like having a professional chef living in your house -- you speak directly to them, there is no waiter, no wait time, and no restaurant overhead. The tradeoff is that only people in your house (your process) can eat.

**Why it matters:** Eliminating the network layer removes serialization/deserialization overhead and enables zero-copy data sharing with host applications. A Python program can pass a Pandas DataFrame to DuckDB and get results back without any data copying.

### 4. Catalog

The [catalog](https://duckdb.org/docs/stable/sql/information_schema) is DuckDB's metadata registry. It tracks schemas, tables, views, functions, types, and extensions. When you write `SELECT * FROM sales`, the catalog resolves "sales" to a specific table with known columns and types.

**Analogy:** The catalog is like a library's card catalog or index system. Before you can find a book (table), you look it up in the catalog to discover where it is, what it contains, and how it is organized. Without the catalog, the database would not know what tables exist or what types their columns have.

**Why it matters:** The binder stage of query processing consults the catalog to resolve table names, verify column existence, determine data types, and check permissions. The catalog also manages extensions and user-defined functions.

### 5. SQL Dialect

DuckDB implements a rich, PostgreSQL-compatible [SQL dialect](https://duckdb.org/docs/stable/sql/introduction) with modern extensions. It supports standard SQL features like window functions, CTEs (WITH clauses), UNNEST, PIVOT/UNPIVOT, recursive queries, and advanced aggregation (GROUPING SETS, CUBE, ROLLUP). It also includes convenience features like `SELECT * EXCLUDE (column)`, `COLUMNS(regex)` expressions, and friendly syntax for common operations.

**Analogy:** If SQL dialects were spoken languages, PostgreSQL SQL would be like formal English, MySQL would be like American English with some slang, and DuckDB would be like a polyglot who speaks formal English fluently but also knows useful shortcuts from other languages. You can write standard SQL and it works, but DuckDB also understands convenient shorthand that saves you typing.

**Why it matters:** DuckDB's parser is derived from PostgreSQL's parser, giving it robust SQL compatibility. The friendly extensions (like `FROM table_name` without SELECT, or auto-completing column names) make interactive data exploration faster and less error-prone.

### 6. Extensions

[Extensions](https://duckdb.org/docs/stable/extensions/overview) are loadable modules that add new functionality to DuckDB without bloating the core binary. They can add new data types, file formats (Parquet, JSON, Excel), network protocols (HTTP, S3), functions, or entire storage backends (Iceberg, Delta Lake).

**Analogy:** Extensions are like apps on a smartphone. The phone (DuckDB core) comes with essential capabilities out of the box, but you can install apps (extensions) to add new abilities -- a map app (spatial extension), a translator (ICU for Unicode collation), or a cloud storage app (httpfs for reading from S3). You only install what you need, keeping the base installation lean.

**Why it matters:** DuckDB ships with ~24 core extensions and has over 100 community extensions as of 2025. Key extensions include `parquet` (columnar file format), `httpfs` (remote file access), `json` (JSON processing), `spatial` (GIS operations), `iceberg` (Apache Iceberg table support), and `postgres_scanner` (reading from live PostgreSQL databases).

### 7. Parallel Execution

DuckDB uses [morsel-driven parallelism](https://15721.courses.cs.cmu.edu/spring2024/notes/20-duckdb.pdf) to distribute work across all available CPU cores. Data is divided into "morsels" (chunks), and multiple threads process different morsels through the same pipeline simultaneously. Operators like hash joins and aggregations are designed to be parallelism-aware with thread-local state that gets merged at the end.

**Analogy:** Imagine a team sorting a mountain of mail. Instead of one person sorting all letters sequentially, you divide the mail into piles (morsels) and give each team member (thread) their own pile. Each person sorts independently using their own sorting bins (thread-local state). At the end, you merge everyone's sorted bins into the final result. The key insight is that each person works independently without waiting for others, maximizing throughput.

**Why it matters:** Modern machines have many CPU cores. DuckDB's parallelism model scales nearly linearly with core count for most analytical queries, turning a 10-second single-threaded query into a 1-second query on a 10-core machine. The morsel-driven approach avoids the overhead of traditional exchange-based parallelism used by server databases.
