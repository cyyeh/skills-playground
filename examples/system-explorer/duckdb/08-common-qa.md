## Common Q&A
<!-- level: all -->
<!-- references:
- [DuckDB FAQ](https://duckdb.org/faq) | official-docs
- [DuckDB Limits](https://duckdb.org/docs/current/sql/data_types/overview.html) | official-docs
-->

### Q: How does DuckDB handle datasets larger than available RAM?

DuckDB's buffer manager automatically spills intermediate results and hash tables to temporary files on disk when memory is exhausted. This happens transparently — you don't need to configure anything beyond optionally setting `temp_directory`. The system tracks memory usage across all operators and evicts cold buffers using a clock-based replacement policy.

However, "out-of-core" doesn't mean "free." Spilling to disk introduces I/O overhead. For optimal performance, size your `memory_limit` to fit the working set of your queries (the hash tables, sort buffers, and intermediate results — not the full dataset). DuckDB's columnar scans are already streaming — it doesn't need to load the entire table into memory to scan it.

Practical guideline: DuckDB comfortably processes datasets 2–5× larger than RAM for most query patterns. For extreme cases (50× RAM), expect significant performance degradation as spilling dominates.

### Q: Can I use DuckDB in a multi-process production environment?

Yes, with constraints. Multiple processes can open the same DuckDB file in `READ_ONLY` mode concurrently — this is the recommended pattern for read-heavy production workloads. For writes, only one process can hold a write lock at a time.

If you need concurrent read-write access from multiple services, consider:
1. **Single-writer pattern:** One process writes, others read in `READ_ONLY` mode
2. **MotherDuck:** Cloud-hosted DuckDB with proper concurrency management
3. **Export to Parquet:** Write results as Parquet files, query them from multiple processes without locking

DuckDB is not designed to be a shared multi-tenant database server. It's an embedded engine — think "one DuckDB per application instance."

### Q: What's the actual performance difference between DuckDB and pandas for analytical operations?

For aggregation-heavy workloads, DuckDB is typically 5–50× faster than pandas, depending on the operation. Key reasons:
- DuckDB processes data in compiled vectorized C++ code; pandas uses Python-level dispatch with NumPy
- DuckDB's columnar engine handles string operations more efficiently (FSST compression, dictionary encoding)
- DuckDB automatically parallelizes across all cores; pandas is largely single-threaded
- DuckDB can query files directly without loading the entire dataset into memory

The gap is largest for operations like GROUP BY with many groups, string-heavy aggregations, and multi-table joins. For simple numeric operations on small datasets (< 100K rows), pandas is competitive because the overhead of query parsing and planning dominates.

DuckDB can also query pandas DataFrames directly via Arrow with zero copy, so you don't have to choose — use DuckDB for the heavy SQL operations and pandas for the rest.

### Q: How does DuckDB's storage format compare to Parquet, and when should I use each?

DuckDB's native `.duckdb` format and Parquet are both columnar, but serve different purposes:

**DuckDB native format** is a read-write database file with ACID transactions, indexes, metadata, and a WAL. Use it when you need: mutable data (INSERT/UPDATE/DELETE), transactional guarantees, or a self-contained database file.

**Parquet** is a read-only file format optimized for interoperability. Use it when you need: data exchange between tools (Spark, Snowflake, Polars), archival storage, or immutable datasets.

In practice, many DuckDB users never use the native format — they query Parquet files directly. DuckDB pushes predicates and column selections into the Parquet reader, so performance is close to native format for read-only workloads. The native format wins when you need write operations or when repeated queries benefit from DuckDB's own compression and metadata.

### Q: What happens during a checkpoint, and how does non-blocking checkpointing (v1.5.0+) work?

A checkpoint compacts the write-ahead log (WAL) into the main database file. Before v1.5.0, checkpoints blocked all reads and writes. Since v1.5.0, checkpointing is non-blocking:

1. The checkpoint process reads the WAL entries and writes them to new blocks in the database file
2. Concurrent reads continue to use the existing data blocks (MVCC ensures they see a consistent snapshot)
3. Concurrent writes continue to append to the WAL
4. Once the checkpoint writes are complete, the system atomically switches to the new blocks
5. The old WAL entries are discarded

This yields ~17% throughput improvement on mixed read-write workloads (measured on TPC-H).

Auto-checkpoint triggers when the WAL exceeds `wal_autocheckpoint` (default: 16MB). You can also manually checkpoint with `CHECKPOINT` or `FORCE CHECKPOINT`.

### Q: How do I debug slow queries in DuckDB?

DuckDB provides multiple profiling tools:

```sql
-- Visual query plan (no execution)
EXPLAIN SELECT ...;

-- Actual execution with timing and row counts
EXPLAIN ANALYZE SELECT ...;

-- Enable detailed profiling
PRAGMA enable_profiling;
PRAGMA enable_progress_bar;
PRAGMA profiling_output = '/tmp/profile.json';
```

Common causes of slow queries:
1. **No predicate pushdown** — Check if filters are pushed into the scan (visible in EXPLAIN). If not, the optimizer may not be able to push the filter (e.g., filter on a computed column).
2. **Spill to disk** — Check `SELECT * FROM duckdb_temporary_files()`. If data is spilling, increase `memory_limit` or simplify the query.
3. **String-heavy operations** — String comparisons are slower than numeric. Consider dictionary encoding or using ENUM types for low-cardinality strings.
4. **Cross joins** — Accidental cross products from missing join conditions. Check row counts with EXPLAIN ANALYZE.

### Q: How does DuckDB compare to ClickHouse for analytical workloads?

DuckDB and ClickHouse occupy different niches:

**DuckDB** is embedded (in-process), single-node, zero-configuration, and excels at interactive ad-hoc analytics on datasets up to ~100GB. No server, no deployment, just `import duckdb`. Ideal for data science, local pipelines, and embedded applications.

**ClickHouse** is a client-server distributed database designed for high-throughput ingestion and sub-second queries on petabytes of data. It requires server deployment, cluster management, and operational expertise. Ideal for production analytics platforms, log analytics, and real-time dashboards at scale.

Choose DuckDB when: single-user, local data, simplicity matters, data fits on one machine.
Choose ClickHouse when: multi-user, continuous ingestion, high-concurrency queries, data spans multiple TB.

They're complementary — many teams use DuckDB for exploration and development, then ClickHouse for production serving.

### Q: What are the practical limits of DuckDB's single-node architecture?

Based on production deployments and benchmarks:
- **Data size:** Comfortably handles up to ~100GB with good performance. Works up to ~500GB with adequate RAM and SSD. Beyond 1TB, consider distributed alternatives.
- **Concurrent queries:** Handles 10–50 concurrent read queries well. Write concurrency is limited to one writer at a time.
- **Query complexity:** The optimizer handles joins of up to ~20 tables efficiently (DPccp algorithm). Beyond that, it falls back to heuristic ordering.
- **Column count:** No hard limit, but tables with 1000+ columns see diminished optimization effectiveness.
- **String operations:** FSST compression helps, but heavy regex or LIKE operations on large string columns can be CPU-bound.
