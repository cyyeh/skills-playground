## Core Concepts
<!-- level: beginner -->
<!-- references:
- [DuckDB Internals Overview](https://duckdb.org/docs/current/internals/overview.html) | official-docs
- [DuckDB In Depth: How It Works and What Makes It Fast](https://endjin.com/blog/2025/04/duckdb-in-depth-how-it-works-what-makes-it-fast) | blog
- [Morsel-Driven Parallelism Paper](https://db.in.tum.de/~leis/papers/morsels.pdf) | paper
-->

### Columnar Storage

**Definition:** DuckDB stores data by column rather than by row. Instead of keeping each row's fields together on disk, it groups all values of a single column contiguously.

**Analogy:** Imagine a library that organizes books not by title on shelves, but by chapter number — all Chapter 1s together, all Chapter 2s together. If you only need to read Chapter 3 from every book, you go straight to one section instead of pulling every book off the shelf. That's what columnar storage does for analytical queries that only touch a few columns out of many.

**Why it matters:** Analytical queries typically scan millions of rows but only access a handful of columns (`SELECT AVG(price) FROM sales`). Columnar storage means DuckDB reads only the columns you need, skipping everything else. It also compresses dramatically better because similar values (all integers, all dates) are stored together.

### Vectorized Execution

**Definition:** Instead of processing data one row at a time (like traditional databases) or one entire column at a time, DuckDB processes data in small batches called "vectors" — typically [2048 values](https://duckdb.org/docs/current/internals/vector.html) at once.

**Analogy:** Think of a factory assembly line. Processing one widget at a time (row-by-row) wastes time switching between stations. Processing all widgets at once (full column) overwhelms the workbench. DuckDB processes a tray of 2048 widgets at a time — small enough to fit on the workbench (CPU cache), large enough to keep the assembly line humming.

**Why it matters:** Modern CPUs have small, ultra-fast memory caches (L1/L2). A vector of 2048 values fits neatly in these caches, so the CPU can process the entire batch without waiting for slower main memory. The compiler can also auto-vectorize these tight loops into SIMD instructions, processing multiple values in a single CPU cycle.

### DataChunk

**Definition:** A `DataChunk` is DuckDB's fundamental unit of data in the execution engine — a collection of vectors (one per column) that all have the same number of rows. It's the "tray" that moves through the query pipeline.

**Analogy:** If the execution engine is a kitchen, a DataChunk is a serving tray carrying multiple dishes (columns) with the same number of portions (rows). Operators in the pipeline take a tray in, transform the dishes, and pass the tray along.

**Why it matters:** The DataChunk is the interface between every operator in the query pipeline. Every scan, filter, join, and aggregation works by receiving DataChunks, transforming them, and passing them forward. This uniform interface keeps the engine modular and cache-friendly.

### Pipeline (Push-Based Execution)

**Definition:** DuckDB uses a [push-based execution model](https://duckdb.org/docs/current/internals/overview.html) where data flows from source operators through intermediate operators to sink operators. A source pushes DataChunks downstream rather than a sink pulling them.

**Analogy:** Picture a series of conveyor belts in a factory. The raw material station (source) pushes parts onto the belt. Each station along the belt (filter, transform) modifies the parts as they pass by. At the end, the packaging station (sink) collects the finished products. The belts keep moving — no station needs to ask for work.

**Why it matters:** Push-based execution enables morsel-driven parallelism. Multiple worker threads can each take a "morsel" (a chunk of input data) from the source and push it through the pipeline independently. This scales linearly with CPU cores without requiring explicit parallel programming.

### Zone Maps (Min-Max Indexes)

**Definition:** For every column in every row group, DuckDB automatically tracks the minimum and maximum values. These metadata statistics are called zone maps.

**Analogy:** Imagine each box in a warehouse has a label saying "contains items priced $5–$20." If you're looking for items over $50, you can skip that entire box without opening it. Zone maps let DuckDB skip entire row groups that can't possibly contain matching data.

**Why it matters:** Zone maps provide free query acceleration for filtered scans. A query like `WHERE date > '2025-01-01'` on a time-ordered dataset can skip most row groups by just checking the min/max metadata — potentially eliminating 99% of I/O before reading a single data value.

### Row Groups

**Definition:** DuckDB organizes table data into row groups — horizontal partitions of roughly 122,880 rows each. Each row group stores its columns independently with separate compression, statistics, and zone maps.

**Analogy:** Think of a filing cabinet where each drawer (row group) holds about 120K records. Each drawer has its own index card on the front (zone maps) telling you the date range inside. You only open drawers that might have what you need, and within each drawer, you only pull the specific file folders (columns) you care about.

**Why it matters:** Row groups are the unit of parallelism and I/O. Different threads can process different row groups concurrently. The size is chosen to balance between parallelism granularity and metadata overhead — large enough to amortize per-group costs, small enough to enable effective pruning and parallel scanning.

### How They Fit Together

When you execute a SQL query, DuckDB's parser converts it to an abstract syntax tree, which the binder resolves against the catalog. The optimizer transforms the logical plan through 30+ optimization passes (including filter pushdown and join reordering). The physical planner then arranges operators into pipelines. During execution, the source operator scans row groups, checking zone maps to skip irrelevant data. It pushes DataChunks (vectors of 2048 values per column) through intermediate operators. Multiple threads run the same pipeline on different row groups simultaneously (morsel-driven parallelism), and the sink operator collects and combines results. The columnar layout ensures only needed columns are read, vectorized execution keeps data in CPU cache, and the push-based pipeline model distributes work across all available cores.
