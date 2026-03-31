## How It Works
<!-- level: intermediate -->
<!-- references:
- [DuckDB Internals Overview](https://duckdb.org/docs/current/internals/overview.html) | official-docs
- [Morsel-Driven Parallelism (SIGMOD 2014)](https://db.in.tum.de/~leis/papers/morsels.pdf) | paper
- [DuckDB In Depth: How It Works](https://endjin.com/blog/2025/04/duckdb-in-depth-how-it-works-what-makes-it-fast) | blog
- [DuckDB Storage & Compression](https://duckdb.org/docs/current/internals/storage.html) | official-docs
-->

### Vectorized Query Processing

DuckDB's execution engine processes data in vectors of `STANDARD_VECTOR_SIZE` (2048) values. Every operator in the pipeline receives a `DataChunk` — a collection of `Vector` objects, one per column — and produces a transformed `DataChunk` as output.

Each `Vector` stores its data in a flat array optimized for CPU cache access. When the engine executes a filter like `WHERE price > 100`, it doesn't check one row at a time. Instead, it runs a tight loop comparing 2048 price values against 100 in a single batch. Modern compilers auto-vectorize these loops into SIMD instructions (SSE, AVX), processing 4–8 comparisons per CPU cycle.

The key insight is the size choice: 2048 values of 8 bytes each = 16KB, which fits comfortably in L1 cache (typically 32–64KB per core). This means the CPU processes the entire vector without cache misses, achieving near-theoretical throughput.

DuckDB uses multiple vector representations to avoid unnecessary data copying:
- **Flat vectors** — contiguous arrays, the most common and fastest format
- **Constant vectors** — a single value repeated for all rows (e.g., the literal `100` in `price > 100`)
- **Dictionary vectors** — indices into a dictionary of unique values, used for compressed string data
- **Sequence vectors** — arithmetically generated sequences (e.g., `rowid`)

### Push-Based Pipeline Execution

DuckDB's executor arranges physical operators into **pipelines** — chains of operators that process data without materializing intermediate results. Each pipeline has:

- A **source** that produces DataChunks (e.g., a table scan)
- Zero or more **intermediate operators** that transform DataChunks in-place (e.g., filter, projection)
- A **sink** that consumes DataChunks and builds state (e.g., hash table for aggregation, sort buffer for ORDER BY)

Pipeline **breaks** occur at operators that must see all input before producing output — hash joins (build side), aggregations, sorts, and window functions. These operators become the sink of one pipeline and the source of the next.

For the query `SELECT region, SUM(amount) FROM sales WHERE year = 2025 GROUP BY region ORDER BY SUM(amount)`:
- **Pipeline 1:** TableScan → Filter → HashAggregate (build) — parallel, each thread scans different row groups
- **Pipeline 2:** HashAggregate (scan) → Sort (build) — reads aggregated results, sorts them
- **Pipeline 3:** Sort (scan) → ResultCollector — produces final ordered output

### Morsel-Driven Parallelism

DuckDB parallelizes query execution using the [morsel-driven model](https://db.in.tum.de/~leis/papers/morsels.pdf). Instead of partitioning data upfront or using exchange operators (like Spark), DuckDB uses a dynamic work-stealing approach:

1. The source operator divides its input into **morsels** (chunks of row groups)
2. Worker threads from the task scheduler each grab a morsel
3. Each thread pushes its morsel through the entire pipeline independently
4. Threads share the same sink state (e.g., a concurrent hash table) using thread-local partitions that are merged at the end

This design scales linearly with CPU cores because:
- No synchronization between threads during pipeline execution (each thread has its own pipeline executor state)
- Work is dynamically distributed — fast threads grab more morsels, naturally load-balancing
- The task scheduler limits concurrency to available hardware threads, avoiding over-subscription

The `Pipeline::ScheduleParallel()` method checks that all operators in the chain support parallelism before enabling multi-threaded execution. If any operator requires ordered processing, the pipeline falls back to sequential execution.

### Storage Engine

DuckDB uses a custom single-file storage format designed for analytical access patterns:

**Block-Based I/O:** The fundamental I/O unit is a 256KB block. This size balances sequential read performance (large enough for SSDs/HDDs to read efficiently) with memory management granularity (small enough to manage in a buffer pool).

**Row Groups:** Tables are horizontally partitioned into row groups of ~122,880 rows (60 × STANDARD_VECTOR_SIZE). Each row group stores columns independently with:
- Per-column compression (lightweight codecs: constant, RLE, dictionary, bitpacking, FSST for strings, Chimp/Patas for floats, ALP for doubles)
- Per-column zone maps (min/max statistics) for predicate pushdown
- Per-column null bitmasks

**Buffer Manager:** DuckDB includes a unified buffer manager that enables out-of-core processing. When available memory is exhausted, the buffer manager transparently spills data to disk using temporary files. This means DuckDB can process datasets significantly larger than RAM — the system handles the spilling automatically with no user configuration.

**Write-Ahead Log (WAL):** For persistent databases, DuckDB uses a WAL for crash recovery. Writes go to the WAL first, and periodic checkpoints compact the WAL into the main database file. Since v1.5.0, checkpointing is non-blocking — reads and writes can proceed concurrently during checkpoint operations, improving throughput by ~17% on mixed workloads.

**Compression:** DuckDB automatically selects the best compression codec per column segment based on data characteristics:
- **Constant** — all identical values (stores one value)
- **RLE (Run-Length Encoding)** — consecutive repeated values
- **Dictionary** — low-cardinality columns (stores unique values + indices)
- **Bitpacking** — integers with limited range (uses minimal bits per value)
- **FSST (Fast Static Symbol Table)** — string compression achieving 2–5× compression
- **Chimp/Patas** — floating-point compression for time-series data
- **ALP (Adaptive Lossless floating-Point)** — double-precision compression

### Query Optimizer Internals

The optimizer runs 30+ passes sequentially on the logical plan. Key passes include:

**Filter Pushdown** pushes predicates as close to the data source as possible. For a query joining two tables with a filter on one, the optimizer moves the filter below the join so it's applied during the scan — reducing the number of rows that enter the join.

**Join Order Optimization** uses the DPccp (Dynamic Programming connected complement pair) algorithm, which efficiently enumerates all valid join orderings for up to ~20 tables. For larger joins, it falls back to heuristics. The optimizer also converts cross products into joins when possible and determines the build/probe sides for hash joins based on estimated cardinalities.

**Late Materialization** defers reading column data until it's actually needed. When a scan has a selective filter, DuckDB first scans only the filtered column, determines which rows pass, and then reads the remaining columns for only those rows. This can dramatically reduce I/O for queries with selective predicates on wide tables.

**Statistics Propagation** maintains cardinality estimates as the plan transforms. Each optimizer pass updates these estimates, which downstream passes use to make better decisions (e.g., which side of a join to use as the build side for a hash join).

### Performance Characteristics

**Where it's fast:**
- Full table scans with aggregation — columnar storage + vectorized execution + automatic parallelism make DuckDB extremely fast for analytical queries. On TPC-H benchmarks, DuckDB competes with dedicated analytical databases like ClickHouse and Hyper.
- Parquet/CSV file queries — DuckDB can query Parquet files directly without loading, using column pruning and predicate pushdown into the file format. Processing a 2GB CSV with 50M rows takes under 3 seconds for aggregation queries.
- Joins on moderate-sized datasets — the hash join implementation is highly optimized with partitioned build/probe and vectorized probing.

**Where it's slower:**
- Point lookups by primary key — DuckDB doesn't have B-tree indexes for OLTP-style lookups. SQLite is ~4× faster for single-record retrieval.
- High-concurrency OLTP workloads — DuckDB uses MVCC for transactions but is not optimized for hundreds of concurrent read-write transactions.
- Very large datasets (multi-TB) — while DuckDB handles out-of-core processing, truly massive datasets benefit from distributed systems like Spark or ClickHouse that spread data across multiple machines.
