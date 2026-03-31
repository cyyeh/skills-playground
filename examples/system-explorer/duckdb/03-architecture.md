## Architecture

<!-- level: intermediate -->

<!-- references:
- https://duckdb.org/docs/current/internals/overview.html
- https://15721.courses.cs.cmu.edu/spring2024/notes/20-duckdb.pdf
- https://endjin.com/blog/2025/04/duckdb-in-depth-how-it-works-what-makes-it-fast
- https://thinhdanggroup.github.io/duckdb/
- https://duckdb.org/2024/07/09/memory-management
-->

### High-Level Design

DuckDB follows a classic layered database architecture, but with a key twist: everything runs in-process. There is no network layer, no wire protocol, and no separate server. The entire system -- from SQL parsing to disk I/O -- executes within the host application's address space.

The query processing pipeline flows through six main stages:

```
SQL String
    |
    v
[ Parser ] --- Converts SQL text to abstract syntax tree (AST)
    |
    v
[ Binder ] --- Resolves names, types, and catalog references
    |
    v
[ Logical Planner ] --- Builds a tree of logical operators
    |
    v
[ Optimizer ] --- Rewrites the plan for efficiency (20+ passes)
    |
    v
[ Physical Plan Generator ] --- Maps logical operators to executable operators
    |
    v
[ Execution Engine ] --- Executes using vectorized, push-based, parallel pipelines
    |
    v
[ Storage Layer ] --- Reads/writes columnar data with buffer management
```

### Key Components

#### 1. Parser

**What:** Converts raw SQL strings into an abstract syntax tree (AST) of `SQLStatement`, `QueryNode`, `TableRef`, and `ParsedExpression` objects.

**Why it exists:** The parser separates syntax analysis from semantic analysis. By producing a database-agnostic AST, it allows the rest of the pipeline to work with structured objects rather than raw text. DuckDB's parser is derived from [PostgreSQL's parser](https://www.postgresql.org/docs/current/parser-stage.html), giving it battle-tested SQL compatibility, but it adds DuckDB-specific syntax like `SELECT * EXCLUDE`, `PIVOT`, and extension-defined statements.

**Key design decision:** The parser is deliberately unaware of the catalog. It does not know what tables exist or what types columns have. This separation means parsing is fast (no catalog lookups) and allows extension parsers to handle custom SQL syntax that the core parser does not recognize.

#### 2. Binder

**What:** Takes the parser's unresolved AST and resolves every reference against the catalog. Tables become concrete catalog entries, column names become typed references, and expressions get their data types determined.

**Why it exists:** SQL is declarative -- users name things by identifier, not by memory address. The binder bridges the gap between human-readable SQL and the internal typed representation the planner needs. It transforms `ParsedExpression` into `Expression` (with resolved types), verifies that referenced tables and columns exist, and extracts aggregate/window functions from expression trees into their own operator nodes.

**Key design decision:** The binder performs full type resolution early, before any optimization. This means the optimizer can reason about types, enabling type-specific optimizations (e.g., integer comparisons are cheaper than string comparisons).

#### 3. Logical Planner

**What:** Converts bound statements into a tree of `LogicalOperator` nodes -- abstract representations of relational operations like Scan, Filter, Join, Aggregate, and Sort.

**Why it exists:** The logical plan represents *what* the query does, not *how* it does it. This abstraction allows the optimizer to freely restructure the plan (reorder joins, push down filters, eliminate unused columns) without worrying about physical execution details.

#### 4. Optimizer

**What:** Applies 20+ optimization passes to the logical plan, transforming it into an equivalent but more efficient plan.

**Why it exists:** Naive query plans can be orders of magnitude slower than optimized ones. A query joining three tables might have 6 possible join orderings, and picking the right one can mean the difference between milliseconds and minutes.

**Key optimization passes include:**

| Pass | Purpose |
|------|---------|
| **Filter Pushdown** | Moves filter predicates closer to data sources to reduce intermediate result sizes early |
| **Join Order Optimization** | Uses the DPccp dynamic programming algorithm to find the optimal join ordering |
| **Projection Pullup** | Removes columns that are never used downstream |
| **Common Subexpression Elimination** | Identifies and shares repeated expression computations |
| **Aggregate Function Rewriting** | Transforms aggregates for efficiency (e.g., `AVG(x)` becomes `SUM(x)/COUNT(x)`) |
| **CTE Inlining** | Inlines Common Table Expressions when materialization would be wasteful |
| **TopN Optimization** | Converts `ORDER BY ... LIMIT N` into a single TopN operator that avoids full sorting |
| **Statistics Propagation** | Gathers and propagates column statistics to inform downstream decisions |
| **Row Group Pruning** | Eliminates entire storage row groups based on min/max metadata |
| **Late Materialization** | Defers reading columns until they are actually needed |

**Key design decision:** The optimizer runs passes in a carefully ordered sequence, and some passes (like CTE inlining and column lifetime analysis) run twice -- once early and once late -- because earlier passes may create new optimization opportunities.

#### 5. Physical Plan Generator

**What:** Transforms the optimized `LogicalOperator` tree into a tree of `PhysicalOperator` nodes that can be directly executed. This is where abstract "Join" becomes a concrete "Hash Join" or "Merge Join," and abstract "Scan" becomes a concrete "Sequential Scan" or "Index Scan."

**Why it exists:** Multiple physical strategies can implement the same logical operation. The generator picks the best physical strategy based on data characteristics -- for example, choosing a hash join for equality predicates and a nested loop join for inequality predicates.

**Key design decision:** The generator supports extension operators. Third-party extensions can define custom `LogicalOperator` types and provide their own physical plan implementations via `CreatePlan()`, enabling extensibility without modifying core code.

#### 6. Execution Engine

**What:** Executes the physical plan using a push-based, vectorized, morsel-driven parallel model. Data flows as `DataChunk` objects (collections of `Vector` columns, each holding up to 2048 values) through a pipeline of operators.

**Why it exists:** The execution engine is where performance is realized. By processing data in vectors (not rows) and pushing data through pipelines (not pulling), DuckDB maximizes CPU cache utilization and minimizes function call overhead.

**Key design decisions:**
- **Push-based model:** Operators push `DataChunk` results to their parent, which avoids the overhead of virtual function calls in pull-based (Volcano-style) iterators.
- **Pipeline-based execution:** The physical plan is decomposed into pipelines separated by "pipeline breakers" (operators that must see all input before producing output, like hash joins or sorts). Each pipeline can execute independently.
- **Morsel-driven parallelism:** Within a pipeline, work is divided into morsels and distributed to threads dynamically, achieving good load balancing without upfront partitioning.

#### 7. Storage Layer

**What:** Manages persistent and in-memory data storage using a single-file format. Data is organized in row groups (collections of columns), with each column stored as compressed segments. The buffer manager handles caching, memory limits, and spilling to disk.

**Why it exists:** The storage layer must efficiently serve the vectorized execution engine with columnar data while managing memory constraints, persistence, crash recovery (via WAL), and concurrent access.

**Key design decisions:**
- **Single-file database:** Like SQLite, a DuckDB database is a single file, making it portable and easy to manage.
- **256 KB blocks:** The fundamental I/O unit -- large enough for efficient sequential reads but small enough for fine-grained memory management.
- **Unified buffer pool:** The buffer manager maintains a single pool for both persistent data pages and temporary intermediate results, allowing dynamic adaptation to workload characteristics.
- **Write-Ahead Log (WAL):** Ensures crash recovery with checkpoint-based persistence.

### Data Flow Through the System

A typical analytical query flows through the system as follows:

1. **User submits SQL** via the C/Python/R API (e.g., `duckdb.sql("SELECT region, SUM(sales) FROM orders GROUP BY region")`)
2. **Parser** produces an AST with a `SelectStatement` containing a `GroupByNode`
3. **Binder** resolves `orders` to a catalog table entry, verifies `region` and `sales` columns exist, and determines their types
4. **Logical Planner** creates: `LogicalAggregate` -> `LogicalGet(orders)`
5. **Optimizer** pushes any filters down, prunes unused columns, chooses statistics-informed strategies
6. **Physical Plan Generator** creates: `PhysicalHashAggregate` -> `PhysicalTableScan(orders)`
7. **Execution Engine** scans the `orders` table in parallel morsels, each thread computing partial aggregates in thread-local hash tables, then merging results
8. **Results** are returned as a materialized result set or streamed back to the caller
