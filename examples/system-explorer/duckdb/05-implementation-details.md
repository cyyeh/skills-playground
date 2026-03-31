## Implementation Details

<!-- level: advanced -->

<!-- references:
- https://duckdb.org/docs/stable/installation/
- https://duckdb.org/docs/stable/api/python/overview
- https://github.com/duckdb/duckdb
- https://duckdb.org/docs/stable/internals/overview
- https://duckdb.org/docs/stable/internals/vector
-->

### Getting Started

#### Installation

DuckDB is available through all major package managers with zero external dependencies:

```bash
# Python (most popular)
pip install duckdb

# R
install.packages("duckdb")

# Node.js
npm install duckdb

# Homebrew (macOS/Linux CLI)
brew install duckdb

# Rust
cargo add duckdb

# Or download the CLI binary directly
# https://duckdb.org/docs/installation/
```

#### Verify Installation

```python
import duckdb
print(duckdb.query("SELECT version()").fetchall())
# [('v1.5.1',)]
```

### Configuration Essentials

DuckDB can be configured per-connection using `SET` statements or via the API:

```sql
-- Memory management
SET memory_limit = '8GB';
SET threads = 4;
SET temp_directory = '/tmp/duckdb_temp';

-- Performance tuning
SET enable_progress_bar = true;
SET enable_object_cache = true;

-- Output formatting
SET max_expression_depth = 1000;

-- Extension management
SET autoinstall_known_extensions = true;
SET autoload_known_extensions = true;
```

Key configuration parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `memory_limit` | 80% of RAM | Maximum memory usage for the buffer pool |
| `threads` | # of CPU cores | Number of worker threads for parallel execution |
| `temp_directory` | `<db_file>.tmp` | Directory for spilling intermediate results to disk |
| `max_temp_directory_size` | 90% of disk | Maximum size of temporary spill files |
| `default_order` | `ASC` | Default sort order |
| `null_order` | `NULLS LAST` | Default NULL ordering in sorts |

### Code Patterns

#### Python: Basic Query Execution

```python
import duckdb

# In-memory database (default)
con = duckdb.connect()

# Query CSV files directly -- no import step needed
result = con.sql("""
    SELECT region, 
           COUNT(*) as num_orders,
           SUM(amount) as total_sales,
           AVG(amount) as avg_order
    FROM 'sales_2025.csv'
    WHERE amount > 0
    GROUP BY region
    ORDER BY total_sales DESC
""").fetchdf()  # Returns a Pandas DataFrame

print(result)
```

#### Python: Parquet and Multi-File Queries

```python
import duckdb

# Query Parquet files with glob patterns
con = duckdb.connect()

# Read all Parquet files in a directory
result = con.sql("""
    SELECT date_trunc('month', order_date) as month,
           SUM(revenue) as monthly_revenue
    FROM 'data/orders/**/*.parquet'
    GROUP BY month
    ORDER BY month
""").fetchdf()

# Query remote Parquet files from S3
con.sql("INSTALL httpfs; LOAD httpfs;")
con.sql("SET s3_region = 'us-east-1';")
remote_data = con.sql("""
    SELECT * FROM 's3://my-bucket/data/events.parquet'
    WHERE event_date >= '2025-01-01'
""").fetchdf()
```

#### Python: Zero-Copy Integration with DataFrames

```python
import duckdb
import pandas as pd

# Create a Pandas DataFrame
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'Diana'],
    'department': ['Eng', 'Sales', 'Eng', 'Sales'],
    'salary': [120000, 95000, 110000, 98000]
})

# Query the DataFrame directly with SQL -- zero-copy!
result = duckdb.sql("""
    SELECT department, 
           AVG(salary) as avg_salary,
           COUNT(*) as headcount
    FROM df
    GROUP BY department
""").fetchdf()
```

#### Python: Persistent Database

```python
import duckdb

# Persistent database -- data survives process restarts
con = duckdb.connect('my_analytics.duckdb')

# Create a table
con.sql("""
    CREATE TABLE IF NOT EXISTS events (
        event_id INTEGER,
        user_id INTEGER,
        event_type VARCHAR,
        timestamp TIMESTAMP,
        properties JSON
    )
""")

# Load data from CSV into the table
con.sql("""
    INSERT INTO events
    SELECT * FROM read_csv('events_*.csv', auto_detect=true)
""")

# Query with window functions
con.sql("""
    SELECT user_id,
           event_type,
           timestamp,
           LAG(timestamp) OVER (PARTITION BY user_id ORDER BY timestamp) as prev_event,
           timestamp - LAG(timestamp) OVER (PARTITION BY user_id ORDER BY timestamp) as time_gap
    FROM events
    WHERE event_type IN ('purchase', 'cart_add')
    ORDER BY user_id, timestamp
""").show()

con.close()
```

#### SQL: Advanced Features

```sql
-- PIVOT: Transform rows to columns
PIVOT monthly_sales
ON month
USING SUM(revenue)
GROUP BY region;

-- UNPIVOT: Transform columns to rows
UNPIVOT quarterly_data
ON q1, q2, q3, q4
INTO NAME quarter VALUE revenue;

-- COLUMNS expression: Apply operations to matching columns
SELECT MIN(COLUMNS('.*_price')) FROM products;

-- Recursive CTE: Graph traversal
WITH RECURSIVE org_chart AS (
    SELECT id, name, manager_id, 1 as depth
    FROM employees WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.name, e.manager_id, oc.depth + 1
    FROM employees e JOIN org_chart oc ON e.manager_id = oc.id
)
SELECT * FROM org_chart ORDER BY depth, name;

-- List comprehension-style syntax
SELECT [x * 2 FOR x IN range(10) IF x % 2 = 0] AS even_doubles;

-- FROM-first syntax (no SELECT needed for exploration)
FROM orders WHERE amount > 1000 LIMIT 10;
```

### Source Code Walkthrough

The DuckDB codebase is organized in `src/` with clear separation of concerns. Below are key code sections from the [duckdb/duckdb](https://github.com/duckdb/duckdb) repository that illustrate the architecture.

#### 1. SQL Parser Entry Point

The parser wraps PostgreSQL's parser and transforms PostgreSQL parse trees into DuckDB's internal representation:

```cpp
void Parser::ParseQuery(const string &query) {
    Transformer transformer(options);
    // Strip unicode spaces (U+00A0, U+2000-U+200B, etc.) to regular spaces
    // to prevent confusing invisible-character bugs
    PostgresParser parser;
    parser.Parse(query);
    if (parser.success) {
        transformer.TransformParseTree(parser.parse_tree, statements);
    }
}
```

```
// source: src/parser/parser.cpp
// github: https://github.com/duckdb/duckdb/blob/main/src/parser/parser.cpp
// tag: v1.5.1
```

This function is the entry point for all SQL processing. The PostgreSQL-derived parser provides robust SQL compatibility, while the `Transformer` translates PostgreSQL AST nodes into DuckDB's own `SQLStatement` hierarchy. Extension parsers can intercept queries the core parser cannot handle.

#### 2. Database Instance Initialization

The `DatabaseInstance::Initialize` method sets up every core subsystem:

```cpp
void DatabaseInstance::Initialize(const char *database_path, DBConfig *user_config) {
    Configure(*config_ptr, database_path);
    db_file_system = make_uniq<DatabaseFileSystem>(*this);
    db_manager = make_uniq<DatabaseManager>(*this);

    if (config.buffer_manager) {
        buffer_manager = config.buffer_manager;
    } else {
        buffer_manager = make_uniq<StandardBufferManager>(*this,
            config.options.temporary_directory);
    }

    log_manager = make_uniq<LogManager>(*this, LogConfig());
    log_manager->Initialize();
    db_manager->InitializeSystemCatalog();
    // Task scheduler initialized after storage to prevent catalog races
}
```

```
// source: src/main/database.cpp
// github: https://github.com/duckdb/duckdb/blob/main/src/main/database.cpp
// tag: v1.5.1
```

This initialization sequence reveals the dependency order: file system first (needed by everything), then buffer manager (needed for memory), then catalog (needs buffer manager), and finally task scheduler (needs catalog to be ready). The buffer manager is injectable, allowing custom implementations.

#### 3. Vectorized Operations Interface

The `VectorOperations` struct defines batch operations on vectors -- the foundation of vectorized execution:

```cpp
struct VectorOperations {
    // Null handling
    static void IsNotNull(Vector &arg, Vector &result, idx_t count);
    static void IsNull(Vector &input, Vector &result, idx_t count);
    static bool HasNull(Vector &input, idx_t count);

    // Boolean logic on vectors
    static void And(Vector &left, Vector &right, Vector &result, idx_t count);
    static void Or(Vector &left, Vector &right, Vector &result, idx_t count);
    static void Not(Vector &left, Vector &result, idx_t count);

    // Comparison operations (with selection vector output)
    static idx_t GreaterThan(Vector &left, Vector &right,
                             optional_ptr<const SelectionVector> sel,
                             idx_t count,
                             optional_ptr<SelectionVector> true_sel,
                             optional_ptr<SelectionVector> false_sel);

    // Hashing and utilities
    static void Hash(Vector &input, Vector &hashes, idx_t count);
    static void Copy(const Vector &source, Vector &target,
                     idx_t source_count, idx_t source_offset);
};
```

```
// source: src/include/duckdb/common/vector_operations/vector_operations.hpp
// github: https://github.com/duckdb/duckdb/blob/main/src/include/duckdb/common/vector_operations/vector_operations.hpp
// tag: v1.5.1
```

Every operation accepts an `idx_t count` parameter, enabling batch processing. The selection-vector variants (`true_sel`/`false_sel`) allow filter operations to produce selection vectors rather than copying data -- a key optimization that avoids unnecessary data movement.

#### 4. Optimizer Pipeline

The optimizer applies a carefully ordered sequence of transformation passes:

```cpp
// Key optimization passes (from optimizer.cpp, in execution order):
// 1. Expression Rewriter     - Constant folding, arithmetic simplification
// 2. Filter Pushdown         - Push filters closer to data sources
// 3. Join Order Optimizer     - DPccp algorithm for optimal join ordering
// 4. CTE Inlining           - Inline CTEs when materialization is wasteful
// 5. Unused Columns Removal  - Drop columns not needed downstream
// 6. Statistics Propagation   - Gather stats for informed decisions
// 7. TopN Optimization        - Convert ORDER BY + LIMIT to TopN
// 8. Common Subexpression     - Share repeated computations
// 9. Row Group Pruning        - Eliminate storage segments via min/max
// 10. Late Materialization    - Defer column reads until needed
// 11. Column Lifetime Analysis - Final projection map cleanup
```

```
// source: src/optimizer/optimizer.cpp
// github: https://github.com/duckdb/duckdb/blob/main/src/optimizer/optimizer.cpp
// tag: v1.5.1
```

The ordering matters: filter pushdown runs before join ordering (so the join optimizer sees reduced cardinalities), and column lifetime analysis runs last (to clean up after all other passes). The optimizer also supports pre- and post-extension hooks.

#### 5. Physical Plan Generation (Logical-to-Physical Mapping)

The `PhysicalPlanGenerator` maps abstract logical operators to concrete physical implementations:

```cpp
PhysicalOperator &PhysicalPlanGenerator::ResolveAndPlan(unique_ptr<LogicalOperator> op) {
    // Step 1: Resolve output types for all operators
    op->ResolveOperatorTypes();

    // Step 2: Convert column bindings to physical indices
    ColumnBindingResolver resolver;
    resolver.VisitOperator(*op);

    // Step 3: Create the physical plan
    physical_plan = PlanInternal(*op);
    return physical_plan->Root();
}

// CreatePlan maps ~40+ logical operator types to physical operators:
// LOGICAL_GET           -> PhysicalTableScan
// LOGICAL_FILTER        -> PhysicalFilter
// LOGICAL_AGGREGATE     -> PhysicalHashAggregate
// LOGICAL_COMPARISON_JOIN -> PhysicalHashJoin or PhysicalMergeJoin
// LOGICAL_ORDER_BY      -> PhysicalSort (or PhysicalTopN if LIMIT present)
// LOGICAL_WINDOW        -> PhysicalWindow
// Extension operators   -> extension_op.CreatePlan(context, *this)
```

```
// source: src/execution/physical_plan_generator.cpp
// github: https://github.com/duckdb/duckdb/blob/main/src/execution/physical_plan_generator.cpp
// tag: v1.5.1
```

The three-step process (type resolution -> column binding -> plan creation) ensures that by the time physical operators are created, all type information is fully resolved and column references are mapped to concrete DataChunk indices.

#### 6. Storage Manager Initialization

The storage manager handles database file creation, loading, and crash recovery:

```cpp
void StorageManager::Initialize(QueryContext context) {
    bool in_memory = InMemory();
    if (in_memory && read_only) {
        throw CatalogException(
            "Cannot launch in-memory database in read-only mode!");
    }
    LoadDatabase(context);
}

// In-memory mode uses a lightweight block manager:
block_manager = make_uniq<InMemoryBlockManager>(
    BufferManager::GetBufferManager(db),
    DEFAULT_BLOCK_ALLOC_SIZE,       // 256 KB
    DEFAULT_BLOCK_HEADER_STORAGE_SIZE);

// Disk-based mode creates/loads the database file and replays the WAL
```

```
// source: src/storage/storage_manager.cpp
// github: https://github.com/duckdb/duckdb/blob/main/src/storage/storage_manager.cpp
// tag: v1.5.1
```

The storage manager selects between `InMemoryBlockManager` (for transient databases) and disk-backed block managers (for persistent `.duckdb` files). The WAL replay on startup ensures crash recovery for persistent databases.

#### 7. Executor and Pipeline Orchestration

The Executor class manages parallel pipeline execution:

```cpp
class Executor {
public:
    explicit Executor(ClientContext &context);

    void Initialize(PhysicalOperator &physical_plan);
    PendingExecutionResult ExecuteTask(bool dry_run = false);
    void WorkOnTasks();  // Process tasks until completion
    bool ExecutionIsFinished();

    // Parallelism management
    void RegisterTask();
    void UnregisterTask();
    void CancelTasks();
    void RescheduleTask(shared_ptr<Task> &task);

    // Progress tracking
    idx_t GetPipelinesProgress(ProgressData &progress);
    idx_t GetCompletedPipelines() const;
    idx_t GetTotalPipelines() const;

    // Error handling
    void PushError(ErrorData exception);
    bool HasError();
    void ThrowException();
};
```

```
// source: src/include/duckdb/execution/executor.hpp
// github: https://github.com/duckdb/duckdb/blob/main/src/include/duckdb/execution/executor.hpp
// tag: v1.5.1
```

The Executor decomposes a physical plan into pipelines, creates tasks for each morsel, and distributes them to worker threads via the task scheduler. `ExecuteTask()` is the main entry point called from the client -- it processes one task at a time, allowing cooperative multitasking with the host application.

### Deployment Considerations

#### In-Process vs. MotherDuck

| Aspect | Local DuckDB | MotherDuck (Cloud) |
|--------|-------------|-------------------|
| **Deployment** | Library in your process | Managed cloud service |
| **Data location** | Local disk/memory | Cloud storage |
| **Concurrency** | Single writer, multiple readers | Multi-tenant with isolation |
| **Scaling** | Limited to single machine | Scales with cloud resources |
| **Cost** | Free (MIT license) | Paid service |
| **Use case** | Local analytics, ETL, testing | Team analytics, production dashboards |

#### Resource Planning

- **Memory:** Plan for 80% of RAM as DuckDB's default allocation. For dedicated analytics machines, increase to 90%. For shared systems, set explicit limits.
- **Disk:** The database file is typically 30--50% the size of raw data due to compression. Temporary directory needs space proportional to the largest intermediate result.
- **CPU:** DuckDB scales nearly linearly with cores for parallel queries. On machines with many cores (32+), the default thread count is usually optimal.
- **Concurrency:** DuckDB supports only a single writer process. For multi-user scenarios, consider MotherDuck or placing DuckDB behind an API server that serializes writes.
