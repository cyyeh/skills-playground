## Architecture
<!-- level: intermediate -->
<!-- references:
- [DuckDB Internals Overview](https://duckdb.org/docs/current/internals/overview.html) | official-docs
- [Push-Based Execution in DuckDB (VLDB 2021)](https://www.vldb.org/pvldb/vol14/p2649-raasveldt.pdf) | paper
- [DuckDB: An Architectural Deep Dive](https://thinhdanggroup.github.io/duckdb/) | blog
- [CMU 15-721 Lecture: DuckDB System Analysis](https://15721.courses.cs.cmu.edu/spring2024/notes/20-duckdb.pdf) | paper
-->

### High-Level Design

DuckDB follows a classic database architecture organized as a multi-stage query processing pipeline, but with critical design choices optimized for analytical workloads. The system is a single-process, multi-threaded C++ library with zero external dependencies. Every component — from SQL parsing to storage management — is compiled into a single library that runs inside the host application's process space.

The architecture can be summarized as a pipeline:

```
SQL String → Parser → Binder → Logical Planner → Optimizer → Physical Planner → Executor → Results
```

Data flows through this pipeline for every query, with each stage transforming the representation from human-readable SQL to machine-executable operators working on columnar vectors.

### Key Components

**Parser** — Converts SQL text into an abstract syntax tree (AST). DuckDB uses a fork of PostgreSQL's battle-tested parser, which provides broad SQL compatibility. The parser is completely catalog-unaware — it produces `SQLStatement`, `QueryNode`, `TableRef`, and `ParsedExpression` nodes without resolving any names or types. This separation exists because parsing is a syntactic concern; mixing in catalog lookups would create circular dependencies and make the parser harder to test and extend.

**Binder** — Resolves names and types against the catalog. The binder transforms parsed nodes into bound equivalents (`SQLStatement` → `BoundStatement`, `ParsedExpression` → `Expression`) by looking up table names, resolving column references, checking types, and expanding wildcards (`SELECT *`). The binder exists as a separate stage because name resolution requires catalog state that the parser deliberately avoids — this clean separation allows DuckDB to support features like CTEs, subqueries, and correlated references through a hierarchical binder chain where child binders inherit parent context.

**Logical Planner** — Produces a tree of `LogicalOperator` nodes representing the query's intent without specifying how to execute it. Operators include `LogicalGet` (scan), `LogicalFilter`, `LogicalProjection`, `LogicalAggregate`, `LogicalJoin`, etc. This abstract representation is what the optimizer works on.

**Optimizer** — The heart of query performance. DuckDB runs [30+ sequential optimization passes](https://duckdb.org/docs/current/internals/overview.html) on the logical plan, including:
- **Filter Pushdown** — moves predicates as close to the data source as possible to reduce I/O
- **Join Order Optimization** — uses the DPccp algorithm for dynamic-programming-based join enumeration
- **Column Pruning** — removes columns that are never referenced downstream
- **Common Subexpression Elimination** — deduplicates repeated computation
- **Late Materialization** — defers column reads until they're actually needed
- **Statistics Propagation** — uses cardinality estimates to guide operator selection
- **TopN Optimization** — converts `ORDER BY ... LIMIT N` into a single efficient operator

The optimizer is extensible — extensions can inject custom pre- and post-optimization passes.

**Physical Planner** — Converts the optimized logical plan into a tree of `PhysicalOperator` nodes that specify concrete execution strategies. For example, a `LogicalJoin` might become a `PhysicalHashJoin` or a `PhysicalMergeJoin` depending on the join condition, data sizes, and available indexes. The physical planner also resolves column bindings from logical column references to physical vector indices.

**Executor** — Arranges physical operators into pipelines and schedules them for parallel execution. The executor uses an event-driven model where pipeline completion triggers downstream pipelines. Each pipeline has a source, zero or more intermediate operators, and a sink. Worker threads from the task scheduler each grab a morsel of work and push it through the pipeline independently.

**Catalog** — Manages all database metadata: schemas, tables, views, functions, types, sequences, and extensions. DuckDB supports attaching multiple databases simultaneously (including read-only access to external databases like PostgreSQL, MySQL, and SQLite via extensions), and the catalog provides a unified namespace across all attached databases.

**Storage Engine** — Manages persistent and in-memory data using a single-file format. Data is organized into row groups (~122,880 rows each), with each column in a row group compressed independently. The storage engine includes a buffer manager for out-of-core processing (datasets larger than RAM), a write-ahead log (WAL) for crash recovery, and checkpoint logic for compacting the WAL into the main database file.

**Task Scheduler** — Manages a thread pool that executes pipeline tasks. The scheduler supports both fully parallel pipelines (multiple threads on different data morsels) and sequential pipelines (when operator semantics require ordered execution). It also handles inter-pipeline dependencies through an event system.

### Data Flow

Tracing a query `SELECT region, SUM(amount) FROM sales WHERE year = 2025 GROUP BY region` through the system:

1. **Parser** tokenizes the SQL and produces an AST with a `SelectStatement` containing a `TableRef("sales")`, a `ComparisonExpression(year = 2025)`, and a `FunctionExpression(SUM(amount))`.

2. **Binder** resolves `sales` to a physical table in the catalog, verifies that `region`, `amount`, and `year` columns exist with compatible types, and produces bound expressions with resolved type information.

3. **Logical Planner** creates: `LogicalGet(sales)` → `LogicalFilter(year = 2025)` → `LogicalAggregate(GROUP BY region, SUM(amount))` → `LogicalProjection(region, sum)`.

4. **Optimizer** pushes the `year = 2025` filter down into the scan (eliminating a separate filter operator), prunes unused columns (only `region`, `amount`, `year` are read), and propagates statistics to estimate result cardinalities.

5. **Physical Planner** converts to: `PhysicalTableScan(sales, filter: year=2025, columns: [region, amount, year])` → `PhysicalHashAggregate(GROUP BY region, SUM(amount))`.

6. **Executor** arranges this into two pipelines:
   - Pipeline 1: Scan → Hash Aggregate (build phase). Multiple threads each scan different row groups, checking zone maps to skip groups where `year` max < 2025 or min > 2025, and push DataChunks into the hash table.
   - Pipeline 2: Hash Aggregate (probe phase) → Result. A single thread reads the aggregated hash table and produces the final output.

### Design Decisions

**In-Process over Client-Server:** DuckDB runs inside the application process, eliminating network round-trips and serialization overhead. This was a deliberate choice — analytical queries on local data shouldn't require running a server. The trade-off is that DuckDB isn't designed for concurrent multi-user access (though it supports multiple read-only connections).

**PostgreSQL Parser Fork:** Rather than building a SQL parser from scratch, DuckDB forked PostgreSQL's parser. This provides mature SQL dialect support (CTEs, window functions, lateral joins) with decades of battle-testing. DuckDB is developing an experimental PEG-based parser (introduced in v1.5.0) for better error messages and extensibility, but the PostgreSQL parser remains the production default.

**Push-Based over Pull-Based Execution:** Most databases use pull-based (Volcano) execution where the root operator calls `next()` on children. DuckDB uses push-based execution where sources push data downstream. This eliminates virtual function call overhead per-tuple and enables more natural morsel-driven parallelism — a source can distribute morsels across threads without complex synchronization at every operator boundary.

**Single-File Storage:** The entire database (data, metadata, indexes) lives in a single file, similar to SQLite. This simplifies deployment, backup, and data sharing. The write-ahead log is stored as a separate file during operation but is compacted into the main file during checkpoints.

**Zero External Dependencies:** DuckDB compiles with just a C++17 compiler. All dependencies (compression algorithms, parsers, etc.) are vendored. This was a deliberate decision to make embedding trivial — no package manager conflicts, no shared library version issues, no system library requirements.
