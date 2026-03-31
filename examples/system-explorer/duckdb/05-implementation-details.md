## Implementation Details
<!-- level: advanced -->
<!-- references:
- [DuckDB Getting Started](https://duckdb.org/docs/current/installation/) | official-docs
- [DuckDB Python API](https://duckdb.org/docs/current/clients/python/overview.html) | official-docs
- [DuckDB Configuration](https://duckdb.org/docs/current/configuration/overview.html) | official-docs
- [DuckDB Source Code](https://github.com/duckdb/duckdb) | github
-->

### Getting Started

**Python (most common):**
```bash
pip install duckdb
```

```python
import duckdb

# Query a CSV file directly — no loading step
result = duckdb.sql("SELECT region, SUM(amount) FROM 'sales.csv' GROUP BY region")
result.show()

# Query a Parquet file from S3
duckdb.sql("SELECT * FROM read_parquet('s3://bucket/data/*.parquet') WHERE year = 2025")

# Create a persistent database
con = duckdb.connect('my_data.duckdb')
con.sql("CREATE TABLE users AS SELECT * FROM read_csv('users.csv')")
```

**CLI:**
```bash
# Install via pip (since v1.5.0)
pip install duckdb-cli

# Or via Homebrew
brew install duckdb

# Start interactive shell
duckdb my_database.duckdb
```

**Other languages:** DuckDB has official bindings for C/C++, Java, Node.js, Rust, Go, R, Swift, and WASM (browser). All use the same underlying C API.

### Configuration Essentials

| Setting | Default | What it controls | When to change |
|---------|---------|-----------------|----------------|
| `memory_limit` | 80% of RAM | Maximum memory for query processing | Running on shared machines or containers |
| `threads` | All cores | Number of worker threads | Limiting CPU usage on shared systems |
| `temp_directory` | Auto | Location for spill-to-disk files | Custom temp storage location |
| `access_mode` | `automatic` | Read-only vs read-write | Concurrent readers on same file |
| `default_order` | `asc` | Default sort order | Preference |
| `preserve_insertion_order` | `true` | Whether scans return rows in insert order | Set `false` for ~10% scan speedup |
| `enable_progress_bar` | `true` | Show progress for long queries | Disable in production/scripts |
| `max_memory` | Same as memory_limit | Alias | — |
| `wal_autocheckpoint` | `16MB` | WAL size before auto-checkpoint | Larger = fewer checkpoints, more recovery time |
| `enable_object_cache` | `false` | Cache Parquet metadata across queries | Enable when querying same Parquet files repeatedly |

```sql
-- Set configuration
SET memory_limit = '4GB';
SET threads = 4;
SET temp_directory = '/tmp/duckdb_spill';

-- Check current settings
SELECT * FROM duckdb_settings();
```

### Code Patterns

**Querying files directly (zero-copy scanning):**
```python
import duckdb

# CSV, Parquet, JSON — with glob patterns
duckdb.sql("SELECT * FROM read_parquet('data/**/*.parquet')")
duckdb.sql("SELECT * FROM read_csv('logs/*.csv', auto_detect=true)")
duckdb.sql("SELECT * FROM read_json('events.jsonl')")

# Query pandas DataFrames directly — zero copy via Arrow
import pandas as pd
df = pd.DataFrame({'x': [1, 2, 3], 'y': ['a', 'b', 'c']})
duckdb.sql("SELECT * FROM df WHERE x > 1")
```

**Replacement scans and the relational API:**
```python
import duckdb

# Chain operations with the relational API
rel = (duckdb.sql("SELECT * FROM 'sales.parquet'")
       .filter("year = 2025")
       .aggregate("region, SUM(amount) AS total")
       .order("total DESC")
       .limit(10))

# Convert to pandas, Arrow, or Polars
df = rel.fetchdf()       # pandas DataFrame
tbl = rel.fetch_arrow()  # Arrow Table
```

**Persistent database with ACID transactions:**
```python
con = duckdb.connect('analytics.duckdb')

con.execute("BEGIN TRANSACTION")
con.execute("CREATE TABLE IF NOT EXISTS events (id INT, type VARCHAR, ts TIMESTAMP)")
con.execute("INSERT INTO events SELECT * FROM read_parquet('new_events.parquet')")
con.execute("COMMIT")
```

**Exporting data:**
```sql
-- Export to Parquet (with partitioning)
COPY (SELECT * FROM sales) TO 'output/' (FORMAT PARQUET, PARTITION_BY (year, region));

-- Export to CSV
COPY sales TO 'sales.csv' (HEADER, DELIMITER ',');
```

### Source Code Walkthrough

#### DataChunk — The Execution Engine's Core Data Unit

The `DataChunk` is the most fundamental class in DuckDB's execution engine. Every operator receives and produces DataChunks. The class holds a vector of `Vector` objects (one per column) and tracks the current row count. The design enforces that all vectors in a chunk have the same length, maintaining the columnar invariant.

```cpp
// source: src/include/duckdb/common/types/data_chunk.hpp:43-77
// github: duckdb/duckdb
// tag: v1.5.1
class DataChunk {
public:
	DUCKDB_API DataChunk();
	DUCKDB_API ~DataChunk();

	//! The vectors owned by the DataChunk.
	vector<Vector> data;

public:
	inline idx_t size() const {
		return count;
	}
	inline idx_t ColumnCount() const {
		return data.size();
	}
	inline void SetCardinality(idx_t count_p) {
		D_ASSERT(count_p <= capacity);
		this->count = count_p;
	}
	inline idx_t GetCapacity() const {
		return capacity;
	}

	DUCKDB_API Value GetValue(idx_t col_idx, idx_t index) const;
	DUCKDB_API void SetValue(idx_t col_idx, idx_t index, const Value &val);

	//! Set the DataChunk to reference another data chunk
	DUCKDB_API void Reference(DataChunk &chunk);
	//! Set the DataChunk to own the data of data chunk, destroying the other chunk
	DUCKDB_API void Move(DataChunk &chunk);

	DUCKDB_API void Initialize(Allocator &allocator, const vector<LogicalType> &types,
	                           idx_t capacity = STANDARD_VECTOR_SIZE);
};
```

Note the `STANDARD_VECTOR_SIZE` default capacity — this is the 2048-value batch size that keeps data in L1 cache. The `Reference()` method enables zero-copy data passing between operators (e.g., a filter operator can reference the source chunk and just add a selection vector).

#### Database Initialization — Wiring Components Together

The `DBConfig` constructor reveals every subsystem DuckDB initializes at startup. Each component is created as an independent module — compression, encoding, type management, Arrow interop, collation, indexing, error handling, secrets, HTTP, and extension callbacks.

```cpp
// source: src/main/database.cpp:46-59
// github: duckdb/duckdb
// tag: v1.5.1
DBConfig::DBConfig() {
	compression_functions = make_uniq<CompressionFunctionSet>();
	encoding_functions = make_uniq<EncodingFunctionSet>();
	encoding_functions->Initialize(*this);
	arrow_extensions = make_uniq<ArrowTypeExtensionSet>();
	arrow_extensions->Initialize(*this);
	type_manager = make_uniq<TypeManager>(*this);
	collation_bindings = make_uniq<CollationBinding>();
	index_types = make_uniq<IndexTypeSet>();
	error_manager = make_uniq<ErrorManager>();
	secret_manager = make_uniq<SecretManager>();
	http_util = make_shared_ptr<HTTPUtil>();
	callback_manager = make_uniq<ExtensionCallbackManager>();
}
```

The `DatabaseInstance` destructor (lines 79–103) shows the careful teardown order: attached databases first, then connections, object cache, scheduler, database manager, logger, file cache, result sets, and finally the buffer manager. This ordering prevents use-after-free by ensuring consumers are destroyed before the resources they depend on.

#### Pipeline Task Execution — The Push-Based Model in Action

This is where data actually flows. Each `PipelineTask` creates a `PipelineExecutor` and calls `Execute()`, which pushes DataChunks from the source through operators to the sink. The `PROCESS_PARTIAL` mode allows cooperative scheduling — a task processes a few chunks then yields, letting other tasks (and pipelines) share CPU time.

```cpp
// source: src/parallel/pipeline.cpp:33-66
// github: duckdb/duckdb
// tag: v1.5.1
TaskExecutionResult PipelineTask::ExecuteTask(TaskExecutionMode mode) {
	if (!pipeline_executor) {
		pipeline_executor = make_uniq<PipelineExecutor>(pipeline.GetClientContext(), pipeline);
	}

	pipeline_executor->SetTaskForInterrupts(shared_from_this());

	if (mode == TaskExecutionMode::PROCESS_PARTIAL) {
		auto res = pipeline_executor->Execute(PARTIAL_CHUNK_COUNT);

		switch (res) {
		case PipelineExecuteResult::NOT_FINISHED:
			return TaskExecutionResult::TASK_NOT_FINISHED;
		case PipelineExecuteResult::INTERRUPTED:
			return TaskExecutionResult::TASK_BLOCKED;
		case PipelineExecuteResult::FINISHED:
			break;
		}
	} else {
		auto res = pipeline_executor->Execute();
		switch (res) {
		case PipelineExecuteResult::NOT_FINISHED:
			throw InternalException("Execute without limit should not return NOT_FINISHED");
		case PipelineExecuteResult::INTERRUPTED:
			return TaskExecutionResult::TASK_BLOCKED;
		case PipelineExecuteResult::FINISHED:
			break;
		}
	}

	event->FinishTask();
	pipeline_executor.reset();
	return TaskExecutionResult::TASK_FINISHED;
}
```

Note the three execution states: `NOT_FINISHED` (more work to do), `INTERRUPTED` (blocked on I/O or downstream), and `FINISHED`. This state machine allows the task scheduler to manage hundreds of concurrent pipeline tasks efficiently.

#### Parallel Pipeline Scheduling — Morsel Distribution

The `ScheduleParallel` method shows how DuckDB decides whether and how to parallelize a pipeline. It checks every operator in the chain for parallel support, queries the source for maximum thread count, and respects the sink's partitioning requirements (e.g., ordered output requires batch indexing).

```cpp
// source: src/parallel/pipeline.cpp:100-138
// github: duckdb/duckdb
// tag: v1.5.1
bool Pipeline::ScheduleParallel(shared_ptr<Event> &event) {
	// check if the sink, source and all intermediate operators support parallelism
	if (!sink->ParallelSink()) {
		return false;
	}
	if (!source->ParallelSource()) {
		return false;
	}
	auto max_threads = source_state->MaxThreads();

	for (auto &op_ref : operators) {
		auto &op = op_ref.get();
		if (!op.ParallelOperator()) {
			return false;
		}
		max_threads = MinValue<idx_t>(max_threads, op.op_state->MaxThreads(max_threads));
	}

	auto partition_info = sink->RequiredPartitionInfo();
	if (partition_info.batch_index) {
		if (!source->SupportsPartitioning(OperatorPartitionInfo::BatchIndex())) {
			throw InternalException(
			    "Attempting to schedule a pipeline where the sink requires batch index "
			    "but source does not support it");
		}
	}

	auto &scheduler = TaskScheduler::GetScheduler(executor.context);
	auto active_threads = NumericCast<idx_t>(scheduler.NumberOfThreads());
	if (max_threads > active_threads) {
		max_threads = active_threads;
	}
	return LaunchScanTasks(event, max_threads);
}
```

The key design: parallelism is opt-in per operator. Each operator declares whether it supports parallel execution via `ParallelSink()`, `ParallelSource()`, and `ParallelOperator()`. The minimum thread count across all operators becomes the actual parallelism level — a single sequential operator forces the entire pipeline to be sequential.

#### Physical Plan Generation — Logical to Physical Translation

The `CreatePlan` dispatcher shows how DuckDB translates abstract logical operations into concrete physical execution strategies. Each logical operator type maps to a specialized physical operator through a switch statement. This is where decisions like "use hash join vs. merge join" are made.

```cpp
// source: src/execution/physical_plan_generator.cpp:78-119
// github: duckdb/duckdb
// tag: v1.5.1
PhysicalOperator &PhysicalPlanGenerator::CreatePlan(LogicalOperator &op) {
	switch (op.type) {
	case LogicalOperatorType::LOGICAL_GET:
		return CreatePlan(op.Cast<LogicalGet>());
	case LogicalOperatorType::LOGICAL_PROJECTION:
		return CreatePlan(op.Cast<LogicalProjection>());
	case LogicalOperatorType::LOGICAL_FILTER:
		return CreatePlan(op.Cast<LogicalFilter>());
	case LogicalOperatorType::LOGICAL_AGGREGATE_AND_GROUP_BY:
		return CreatePlan(op.Cast<LogicalAggregate>());
	case LogicalOperatorType::LOGICAL_WINDOW:
		return CreatePlan(op.Cast<LogicalWindow>());
	case LogicalOperatorType::LOGICAL_LIMIT:
		return CreatePlan(op.Cast<LogicalLimit>());
	case LogicalOperatorType::LOGICAL_ORDER_BY:
		return CreatePlan(op.Cast<LogicalOrder>());
	case LogicalOperatorType::LOGICAL_TOP_N:
		return CreatePlan(op.Cast<LogicalTopN>());
	case LogicalOperatorType::LOGICAL_ANY_JOIN:
		return CreatePlan(op.Cast<LogicalAnyJoin>());
	case LogicalOperatorType::LOGICAL_ASOF_JOIN:
	case LogicalOperatorType::LOGICAL_DELIM_JOIN:
	case LogicalOperatorType::LOGICAL_COMPARISON_JOIN:
		return CreatePlan(op.Cast<LogicalComparisonJoin>());
	case LogicalOperatorType::LOGICAL_CROSS_PRODUCT:
		return CreatePlan(op.Cast<LogicalCrossProduct>());
	case LogicalOperatorType::LOGICAL_INSERT:
		return CreatePlan(op.Cast<LogicalInsert>());
	case LogicalOperatorType::LOGICAL_DELETE:
		return CreatePlan(op.Cast<LogicalDelete>());
	case LogicalOperatorType::LOGICAL_UPDATE:
		return CreatePlan(op.Cast<LogicalUpdate>());
	// ... 20+ more operator types
	}
}
```

Each typed `CreatePlan` overload (not shown) makes implementation-specific decisions. For example, `CreatePlan(LogicalComparisonJoin)` chooses between hash join, merge join, nested-loop join, or index join based on join conditions, estimated cardinalities, and available indexes.

#### Binder — Name Resolution Against the Catalog

The Binder constructor shows the hierarchical binder chain that enables subquery and CTE resolution. Each binder inherits its parent's context (catalog entries, macro bindings, lambda bindings), enabling correlated subqueries to reference columns from outer scopes.

```cpp
// source: src/planner/binder.cpp:21-36
// github: duckdb/duckdb
// tag: v1.5.1
Binder::Binder(ClientContext &context, shared_ptr<Binder> parent_p,
    BinderType binder_type)
    : context(context), bind_context(*this), parent(std::move(parent_p)),
      binder_type(binder_type),
      global_binder_state(parent ? parent->global_binder_state :
          make_shared_ptr<GlobalBinderState>()),
      query_binder_state(parent && binder_type == BinderType::REGULAR_BINDER ?
          parent->query_binder_state : make_shared_ptr<QueryBinderState>()),
      entry_retriever(context), depth(parent ? parent->GetBinderDepth() : 1) {
    IncreaseDepth();
    if (parent) {
        entry_retriever.Inherit(parent->entry_retriever);
        macro_binding = parent->macro_binding;
        lambda_bindings = parent->lambda_bindings;
    }
}
```

Note the `depth` tracking with `IncreaseDepth()` — this guards against stack overflow from deeply nested subqueries by enforcing a maximum expression depth limit (configurable via `max_expression_depth`).

### Deployment Considerations

**Sizing:** DuckDB works well with datasets up to ~100GB on a single machine. Set `memory_limit` to 60–80% of available RAM to leave room for the OS and other processes. The buffer manager handles spill-to-disk automatically when memory is exceeded.

**Monitoring:** Use `PRAGMA enable_profiling` and `EXPLAIN ANALYZE` to profile query execution. DuckDB's profiler shows per-operator timing, row counts, and memory usage. The `duckdb_temporary_files()` function reveals spill-to-disk activity.

**Backup:** The database is a single file — copy it. For zero-downtime backup, use `EXPORT DATABASE` which produces a portable set of CSV + SQL files, or `CHECKPOINT` to ensure the WAL is flushed before copying the `.duckdb` file.

**Upgrades:** DuckDB's storage format is forward-compatible within the same major version (1.x). When upgrading across major versions, use `EXPORT DATABASE` before upgrading and `IMPORT DATABASE` after. The v1.4.x LTS line provides long-term stability for production deployments.

**Concurrency:** DuckDB supports multiple concurrent readers but only one writer at a time. For read-heavy production workloads, open the database in `READ_ONLY` mode from multiple processes. For write workloads, funnel writes through a single connection.
