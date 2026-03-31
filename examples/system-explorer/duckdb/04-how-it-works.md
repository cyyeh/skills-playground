## How It Works

<!-- level: intermediate -->

<!-- references:
- https://duckdb.org/docs/stable/internals/vector
- https://duckdb.org/2024/07/09/memory-management
- https://duckdb.org/2024/03/29/external-aggregation
- https://15721.courses.cs.cmu.edu/spring2024/notes/20-duckdb.pdf
- https://endjin.com/blog/2025/04/duckdb-in-depth-how-it-works-what-makes-it-fast
-->

### Vectorized Execution Engine

DuckDB's execution engine is the heart of its performance. Unlike traditional row-at-a-time engines (the Volcano/iterator model used by PostgreSQL and MySQL), DuckDB processes data in **vectors** -- arrays of up to 2048 values per column.

#### How Vectors Work

A [Vector](https://duckdb.org/docs/stable/internals/vector) is a typed array holding values for a single column. A `DataChunk` is a collection of Vectors representing multiple columns -- essentially a small columnar table of up to 2048 rows.

```
DataChunk (e.g., from scanning "orders" table):
+-------------------+-------------------+-------------------+
| Vector: order_id  | Vector: region    | Vector: amount    |
| [1, 2, 3, ... ]   | ["US", "EU", ...] | [99.5, 42.0, ...] |
| (up to 2048 vals) | (up to 2048 vals) | (up to 2048 vals) |
+-------------------+-------------------+-------------------+
```

The vector size of 2048 is deliberately chosen to fit within the CPU's L1 cache (typically 32--128 KB per core). This means that when an operator processes a vector, the data stays in the fastest level of the CPU's memory hierarchy, avoiding expensive L2/L3 cache misses and RAM accesses.

#### Push-Based Processing

DuckDB uses a **push-based** model rather than the traditional pull-based (Volcano) model:

- **Pull-based (Volcano):** Each operator calls `GetNext()` on its child to request one row/batch. Control flow bounces up and down the operator tree with virtual function calls at every level.
- **Push-based (DuckDB):** Source operators produce `DataChunk`s and push them through a pipeline of operators. Each pipeline is compiled into a tight loop with no virtual dispatch overhead between operators.

The push-based approach eliminates per-batch virtual function call overhead and enables better compiler optimizations, since the tight processing loop has predictable control flow.

#### Vector Formats

DuckDB supports multiple physical representations for the same logical data:

| Format | Description | Use Case |
|--------|-------------|----------|
| **FLAT** | Standard contiguous array | Default general-purpose format |
| **CONSTANT** | Single value representing all elements | Literal values, broadcast operations |
| **DICTIONARY** | Index array + dictionary of unique values | Low-cardinality string columns |
| **SEQUENCE** | Start + increment (no array stored) | Row IDs, generated sequences |
| **FSST** | Fast Static Symbol Table compressed | Compressed string data |

These formats allow "compressed execution" -- operations can be performed directly on the compressed representation without decompressing first. For example, filtering a DICTIONARY vector only needs to check the dictionary entries, not every individual value.

#### Performance Characteristics

- **Throughput:** DuckDB processes analytical queries at rates of 1--10 GB/s per core on modern hardware, depending on query complexity
- **Vector processing overhead:** ~0.5 nanoseconds per value per operator (vs ~50 ns for row-at-a-time)
- **Function call reduction:** Processing 2048 values per call reduces function call overhead by ~2000x compared to row-at-a-time
- **Cache efficiency:** L1 cache hit rate exceeds 95% for typical vector operations, compared to ~60-70% for row-based engines on analytical queries

### Morsel-Driven Parallelism

DuckDB parallelizes query execution using [morsel-driven parallelism](https://15721.courses.cs.cmu.edu/spring2023/slides/22-duckdb.pdf), a technique where operators are made parallelism-aware rather than using generic exchange/partition operators.

#### How It Works

1. **Pipeline decomposition:** The physical plan is split into pipelines at "pipeline breaker" points -- operators that must consume all input before producing output (e.g., hash table build side of a join, sort operator, aggregate with GROUP BY)

2. **Morsel distribution:** The source of each pipeline divides its data into morsels (chunks). A central coordinator distributes morsels to worker threads on demand.

3. **Thread-local processing:** Each thread processes its morsel through the pipeline independently, maintaining thread-local state (e.g., thread-local hash tables for aggregation).

4. **Global merge:** After all morsels are processed, thread-local states are merged into a single global result.

```
Pipeline Example: SELECT region, SUM(amount) FROM orders WHERE amount > 100 GROUP BY region

Source (TableScan)
    |
    | morsel 1 -> Thread 1: Filter -> Aggregate (local HT)
    | morsel 2 -> Thread 2: Filter -> Aggregate (local HT)
    | morsel 3 -> Thread 3: Filter -> Aggregate (local HT)
    | morsel 4 -> Thread 1: Filter -> Aggregate (local HT)  (thread 1 picks up more work)
    |
    v
Merge thread-local hash tables -> Final Result
```

#### Why Not Exchange-Based Parallelism?

Traditional databases (like PostgreSQL) use exchange operators that partition data between parallel workers at fixed points in the plan. This approach has drawbacks:
- Fixed partitioning can lead to skewed workloads
- Exchange operators add overhead even for non-parallel plans
- Difficult to adapt parallelism degree dynamically

Morsel-driven parallelism avoids these issues by distributing work dynamically (like a work-stealing scheduler) and keeping operators themselves parallelism-aware, which eliminates exchange overhead.

### Buffer Manager

The [buffer manager](https://duckdb.org/2024/07/09/memory-management) is responsible for all memory management in DuckDB. It maintains a unified pool of memory for both persistent data pages (cached from disk) and temporary data (intermediate results during query execution).

#### Memory Architecture

```
+-----------------------------------------+
|           Buffer Manager                |
|  +-----------------------------------+ |
|  |         Buffer Pool               | |
|  |  +-----------+ +-----------+      | |
|  |  | Persistent| | Temporary |      | |
|  |  | Pages     | | Pages     |      | |
|  |  | (cached   | | (hash     |      | |
|  |  |  table    | |  tables,  |      | |
|  |  |  data)    | |  sorts)   |      | |
|  |  +-----------+ +-----------+      | |
|  +-----------------------------------+ |
|                                         |
|  Eviction Queue (LRU-based)             |
|  Spill-to-Disk (temporary directory)    |
+-----------------------------------------+
```

#### Key Characteristics

- **Default memory limit:** 80% of physical RAM (configurable via `SET memory_limit = '4GB'`)
- **Block size:** 256 KB -- a compromise between sequential read efficiency and memory granularity
- **Unified pool:** Persistent and temporary data share the same pool, allowing DuckDB to adapt dynamically. A read-heavy workload gets more cache; a computation-heavy workload gets more temporary space.
- **Pin/unpin model:** When an operator needs a block, it pins it (preventing eviction). When done, it unpins the block, making it available for eviction if memory pressure arises.
- **Spilling:** When memory is exhausted, the buffer manager evicts unpinned pages to the temporary directory on disk. This enables larger-than-memory queries at the cost of I/O.

#### Larger-Than-Memory Processing

DuckDB handles datasets larger than available memory through three mechanisms:

1. **Streaming execution:** Data sources are never fully materialized. Scan operators read one morsel at a time, process it, and discard it before reading the next.
2. **Intermediate spilling:** When operators like hash aggregation or sorting exceed their memory budget, they spill partitions to temporary files on disk and process them in passes.
3. **Buffer eviction:** The buffer manager can evict cached persistent data pages to make room for active computation.

Configuration for larger-than-memory:
```sql
SET memory_limit = '4GB';
SET temp_directory = '/tmp/duckdb_swap';
SET max_temp_directory_size = '100GB';
```

### Storage Format

DuckDB uses a custom single-file storage format designed for analytical workloads.

#### Physical Layout

Data is organized hierarchically:

```
Database File
  +-- Header (metadata, version info)
  +-- Row Group 1 (default: ~122K rows)
  |     +-- Column Segment: col_A (compressed)
  |     +-- Column Segment: col_B (compressed)
  |     +-- Column Segment: col_C (compressed)
  |     +-- Min/Max Statistics per segment
  +-- Row Group 2
  |     +-- ...
  +-- Catalog (schemas, tables, views)
  +-- Write-Ahead Log (WAL)
```

#### Compression

Each column segment is compressed independently using the best algorithm for its data distribution:

| Algorithm | Best For |
|-----------|----------|
| **Constant** | Columns where all values are the same |
| **RLE (Run-Length Encoding)** | Sorted or clustered data with repeated runs |
| **BitPacking** | Integer columns with small value ranges |
| **Dictionary** | Low-cardinality string columns |
| **FSST (Fast Static Symbol Table)** | High-cardinality string columns |
| **Chimp/Patas** | Floating-point columns |
| **ALP (Adaptive Lossless floating-Point)** | Double-precision floating-point data |

DuckDB automatically selects the best compression algorithm per segment based on data analysis during checkpointing, achieving typical compression ratios of 3--10x on real-world data.

#### Persistence Model

- **In-memory mode:** No file on disk. Data lives only in the process's memory. Fastest but non-persistent.
- **Persistent mode:** Data is written to a single `.duckdb` (or `.db`) file. A Write-Ahead Log (WAL) ensures crash recovery.
- **Checkpoint:** Periodically, DuckDB writes the WAL contents into the main database file and truncates the WAL. Checkpoints happen automatically when the WAL grows beyond a threshold, or can be triggered manually with `CHECKPOINT`.
