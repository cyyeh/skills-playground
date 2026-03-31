## Common Q&A

<!-- level: all -->

<!-- references:
- https://duckdb.org/faq
- https://duckdb.org/docs/stable/connect/concurrency
- https://duckdb.org/2024/07/09/memory-management
- https://duckdb.org/docs/stable/extensions/overview
- https://duckdb.org/docs/stable/operations_manual/limits
-->

### Q1: How much memory does DuckDB use, and can I control it?

**Answer:** By default, DuckDB allocates up to 80% of physical RAM for its buffer pool. This is configurable:

```sql
-- Set a hard memory limit
SET memory_limit = '4GB';

-- Check current memory usage
SELECT * FROM duckdb_memory();

-- Monitor temporary file usage when spilling to disk
SELECT * FROM duckdb_temporary_files();
```

DuckDB's memory is divided between:
- **Buffer pool:** Caches persistent data pages and holds temporary intermediate results (hash tables, sort buffers)
- **Overhead:** Internal data structures, catalog metadata, and connection state (not counted toward the memory limit)

If your query's intermediate results exceed the memory limit, DuckDB spills to the temporary directory on disk. This is automatic but slower than in-memory processing. For purely in-memory workloads, you can set `temp_directory = ''` to disable spilling (queries that exceed memory will fail instead).

---

### Q2: Can multiple processes write to the same DuckDB file concurrently?

**Answer:** No. DuckDB uses a **single-writer** model for file-backed databases:

- **Multiple readers:** Multiple processes can open the same `.duckdb` file in read-only mode simultaneously.
- **Single writer:** Only one process can open a database file in read-write mode at a time. A second process attempting to open the file for writing will block or fail, depending on timeout settings.
- **Within a single process:** Multiple threads can read and write concurrently. DuckDB uses [MVCC (Multi-Version Concurrency Control)](https://en.wikipedia.org/wiki/Multiversion_concurrency_control) with optimistic concurrency control to manage intra-process parallelism.

This design choice exists because DuckDB caches data, function pointers, and catalog metadata in RAM for fast analytical queries. Sharing this state across processes would require complex inter-process coordination that would degrade performance.

**Workarounds for multi-process writes:**
- Use a cross-process mutex lock, with each process opening and closing the database for its write operation
- Use [MotherDuck](https://motherduck.com) for multi-user cloud-based access
- Design your application with a single writer process and multiple reader processes
- Use separate DuckDB files per writer and merge periodically

---

### Q3: What is the difference between in-memory and persistent mode?

**Answer:**

| Aspect | In-Memory Mode | Persistent Mode |
|--------|---------------|-----------------|
| **Creation** | `duckdb.connect()` or `duckdb.connect(':memory:')` | `duckdb.connect('my_db.duckdb')` |
| **Data survival** | Lost when process exits | Survives process restarts |
| **Performance** | Fastest (no disk I/O for data) | Slightly slower (WAL writes, checkpointing) |
| **Storage format** | Same columnar format, but only in RAM | Single `.duckdb` file on disk |
| **Crash recovery** | No recovery (data is lost) | WAL-based recovery on next startup |
| **File size** | N/A | Typically 30-50% of raw data size due to compression |
| **Use case** | Temporary analysis, testing, ETL intermediates | Long-lived databases, reproducible analysis |

You can also attach multiple databases (including both in-memory and persistent) to a single connection:

```sql
ATTACH 'analytics.duckdb' AS analytics;
ATTACH ':memory:' AS scratch;

-- Query across both
SELECT * FROM analytics.sales
JOIN scratch.temp_lookup USING (id);
```

---

### Q4: How does DuckDB handle queries on data larger than available memory?

**Answer:** DuckDB uses three mechanisms to process larger-than-memory datasets:

1. **Streaming execution:** Data sources (CSV, Parquet, tables) are never fully loaded into memory. DuckDB reads and processes data one chunk at a time, discarding processed chunks before reading the next.

2. **Intermediate spilling:** When operators like hash aggregation, hash joins, or sorting produce intermediate results that exceed the memory budget, they partition and spill excess data to temporary files on disk. Processing continues in multiple passes over the spilled partitions.

3. **Buffer eviction:** The buffer manager evicts cached data pages from the buffer pool using an LRU-like policy when memory pressure arises.

**Configuration for larger-than-memory workloads:**

```sql
SET memory_limit = '4GB';                  -- Hard limit
SET temp_directory = '/fast-ssd/duckdb_tmp'; -- Use fast storage for spills
SET max_temp_directory_size = '200GB';       -- Limit disk usage
```

**Important caveats:**
- Not all operators support spilling. Some operations may still fail with out-of-memory errors on extremely large datasets.
- Spilling is significantly slower than in-memory processing (10--100x for I/O-bound operations).
- DuckDB's larger-than-memory support targets occasional overflows, not routine processing of datasets far exceeding RAM.

---

### Q5: Are DuckDB extensions safe? Can they access my filesystem or network?

**Answer:** Extensions run as native code in the same process as DuckDB and have full access to the host system's resources, including the filesystem and network. There is no sandboxing.

**Security considerations:**
- **Signed extensions:** DuckDB core extensions are cryptographically signed by the DuckDB team. By default, DuckDB only loads signed extensions.
- **Unsigned extensions:** Community extensions require explicit opt-in: `SET allow_unsigned_extensions = true`. Only enable this for extensions you trust.
- **Extension sources:** Extensions are downloaded from the official DuckDB extension repository by default. You can configure custom repositories, but this should be done with caution.
- **Filesystem access:** Extensions like `httpfs` can read from remote URLs, and `postgres_scanner` can connect to external databases. Be aware of what network access your extensions might perform.

**Best practice:** In production environments, pin extension versions, only use signed extensions, and audit community extensions before enabling them.

---

### Q6: How does DuckDB compare to Pandas for data analysis?

**Answer:**

| Aspect | DuckDB | Pandas |
|--------|--------|--------|
| **Query language** | SQL | Python DataFrame API |
| **Performance (large data)** | 10--100x faster for aggregations on GB+ datasets | Slow; single-threaded, loads entire dataset into memory |
| **Memory efficiency** | Columnar, compressed, streaming | Row-oriented, uncompressed, eager loading |
| **Parallelism** | Automatic multi-core | Single-threaded (manual parallelism via multiprocessing) |
| **Max practical data size** | 10--100+ GB (with spilling) | ~1-5 GB (limited by RAM) |
| **Ease of use** | SQL (familiar to most analysts) | Python (flexible but verbose for complex joins/windows) |
| **Integration** | Zero-copy with Pandas, Polars, Arrow | Native Python ecosystem |

DuckDB and Pandas are complementary. A common pattern is using DuckDB for heavy lifting (joins, aggregations, filtering) and Pandas for final-mile operations (plotting, ML model input):

```python
import duckdb
# Heavy computation in DuckDB (fast, parallel, memory-efficient)
result = duckdb.sql("""
    SELECT customer_id, SUM(amount), COUNT(*)
    FROM 'large_dataset.parquet'
    GROUP BY customer_id
    HAVING COUNT(*) > 10
""").fetchdf()  # Returns Pandas DataFrame

# Visualization in Pandas/Matplotlib (works on the small result)
result.plot(kind='bar', x='customer_id', y='sum(amount)')
```

---

### Q7: Can I use DuckDB in a web application backend?

**Answer:** Yes, with caveats. DuckDB works well as an embedded analytics engine in web backends:

**Good patterns:**
- Read-only analytics endpoints where DuckDB queries pre-loaded Parquet/database files
- Single-writer architectures where one background process ingests data and API servers open the database read-only
- Per-request in-memory databases for stateless query processing

**Anti-patterns to avoid:**
- Using DuckDB as the primary transactional database for the web app (use PostgreSQL/MySQL instead)
- Multiple API server processes writing to the same `.duckdb` file concurrently
- Expecting high-concurrency transactional performance (DuckDB is optimized for fewer, heavier queries)

**Example architecture:**

```
Data Ingestion Service (single writer)
       |
       | Writes to analytics.duckdb
       v
  analytics.duckdb (on shared filesystem)
       |
       | Read-only connections
       v
API Server 1  API Server 2  API Server 3
(read-only)   (read-only)   (read-only)
```

---

### Q8: What are the hard limits of DuckDB?

**Answer:**

| Resource | Limit |
|----------|-------|
| **Maximum database size** | Limited by available disk space (single-file format) |
| **Maximum in-memory data** | Limited by `memory_limit` setting (default 80% RAM) |
| **Maximum columns per table** | ~100,000 columns (practical limit; no hard cap) |
| **Maximum row group size** | ~122,880 rows per row group |
| **Maximum string length** | ~4 GB per value (stored as BLOB internally) |
| **Maximum query complexity** | Limited by `max_expression_depth` (default 1000) |
| **Concurrent writers** | 1 per database file (per process) |
| **Concurrent readers** | Unlimited (within practical resource limits) |
| **Supported platforms** | Linux, macOS, Windows (x86_64, ARM64), WebAssembly |
| **Extension count** | ~24 core + 100+ community (as of 2025) |

In practice, DuckDB performs best on datasets that fit in memory (up to ~100-200 GB on modern machines). It can handle larger datasets via spilling, but performance degrades for workloads that are significantly larger than available RAM.
