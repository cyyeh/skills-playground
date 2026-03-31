## Architecture
<!-- level: intermediate -->
<!-- references:
- [Qdrant Architecture Overview](https://qdrant.tech/documentation/overview/) | official-docs
- [Qdrant Source Code](https://github.com/qdrant/qdrant) | github
- [Filtrable HNSW - Qdrant](https://qdrant.tech/articles/filtrable-hnsw/) | blog
- [Qdrant 1.16 - Tiered Multitenancy](https://qdrant.tech/blog/qdrant-1.16.x/) | blog
-->

### High-Level Design

Qdrant follows a client-server architecture where the server is a standalone Rust binary exposing REST and gRPC APIs. Unlike embedded databases, Qdrant runs as a separate process (or cluster of processes) that clients connect to over the network. The system is designed around a layered architecture where each layer has a clear responsibility:

```
Client Request --> API Layer (REST/gRPC) --> Collection Manager --> Shard Router --> Local Shard --> Segment Holder --> Segments (Vectors + Payloads + Indexes)
```

Data flows inward from the API through routing and coordination layers to the storage engine, while search results flow outward through merging and ranking. In distributed mode, the shard router forwards requests to remote shards on other nodes, collects partial results, and merges them before returning to the client.

### Key Components

**API Layer (REST & gRPC)** -- Provides two network interfaces for all operations: a RESTful HTTP API for simplicity and a gRPC API for performance-critical workloads. The REST layer uses Actix-web, while gRPC uses Tonic. Both interfaces share the same internal type system defined in the `lib/api` crate, ensuring behavioral parity. The dual-API design exists because REST is universally accessible (any language with an HTTP client works), while gRPC provides binary serialization and streaming for high-throughput ingestion pipelines.

**Collection Manager** -- Manages the lifecycle of collections: creation, deletion, configuration updates, and snapshot management. Each collection holds its configuration (vector parameters, HNSW settings, quantization, optimizer config) and delegates data operations to its shard holder. The collection manager also coordinates distributed operations like shard transfers and replica state changes.

**Shard Holder & Router** -- A collection's data is divided into shards, and the shard holder manages these divisions. When a request arrives, the router determines which shard(s) hold the relevant data (using consistent hashing on point IDs for writes, or broadcasting to all shards for searches). Each shard can have multiple replicas managed as a `ShardReplicaSet`, providing fault tolerance and read scaling.

**Local Shard** -- The workhorse of data storage. A local shard owns a Write-Ahead Log (WAL), a set of segments, and an update handler with optimizers. All writes pass through the WAL for durability before being applied to the appendable segment. The shard coordinates concurrent access to segments using lock-free patterns -- collecting segment references before operations so the segment holder isn't locked during execution.

**Segments** -- The lowest-level storage unit. Each segment is self-contained with its own vector storage, payload storage, payload index, vector index (plain or HNSW), and ID tracker. Segments come in two types: appendable (accepts new points, uses a plain vector index for fast writes) and non-appendable (immutable, HNSW-indexed, possibly quantized, optimized for search). The optimizer continuously converts appendable segments to non-appendable ones and merges small segments.

**Optimizer** -- A background process that monitors segments and triggers optimizations: building HNSW indexes on accumulated data, merging small segments to reduce overhead, applying quantization, and vacuuming deleted points. The optimizer runs asynchronously and never blocks search operations. Multiple optimizer strategies run concurrently: `IndexingOptimizer` builds indexes when segments reach a threshold, `MergeOptimizer` combines small segments, and `VacuumOptimizer` reclaims space from deleted points.

**Consensus (Raft)** -- In distributed deployments, Qdrant uses the Raft consensus protocol to coordinate cluster-wide operations: collection creation/deletion, shard placement, replica management, and configuration changes. Raft ensures that all nodes agree on the cluster state even in the presence of network partitions or node failures. Data operations (upserts, searches) do not go through Raft -- they use direct peer-to-peer communication for performance.

**Write-Ahead Log (WAL)** -- Every write operation is first persisted to the WAL before being applied to segments. This ensures durability: if the process crashes, pending operations can be replayed from the WAL on restart. The WAL is per-shard and uses a custom implementation (`RecoverableWal`) that supports sequential writes and replay.

### Data Flow

Tracing an upsert of a point with vector `[0.1, 0.2, ...]` and payload `{"category": "electronics", "price": 299}`:

1. **API Layer** receives the HTTP PUT request, deserializes the JSON body into internal types, and validates the request (vector dimensionality matches collection config, payload types are valid).

2. **Collection Manager** routes the request to the appropriate collection, which forwards it to the shard holder.

3. **Shard Router** hashes the point ID to determine the target shard. If the target shard is local, the request goes to the local shard. If remote, it's forwarded to the owning node via gRPC.

4. **Local Shard** writes the operation to the WAL for durability, then applies it to the current appendable segment. The point's vector is stored in the vector storage, and the payload is stored in the payload storage.

5. **Payload Index** (if indexes exist on `category` or `price`) updates its indexes to include the new point, enabling fast filtered search.

6. **Optimizer** (background) eventually notices the appendable segment has grown large enough and triggers an optimization pass: it creates a new non-appendable segment by building an HNSW graph over all vectors, applying quantization, and building optimized payload indexes. The old appendable segment is replaced, and a new empty appendable segment is created for future writes.

Tracing a search for `query_vector` with filter `category = "electronics" AND price < 500`:

1. **API Layer** receives the search request and deserializes the query vector, filter, and parameters (limit, `hnsw_ef`, etc.).

2. **Shard Router** broadcasts the search to all shards (searches must check all data).

3. **Each Local Shard** searches all its segments in parallel. For each segment, the query planner evaluates the filter:
   - If the filter matches a large fraction of points: use HNSW graph traversal, skipping non-matching points during traversal (filterable HNSW).
   - If the filter matches a small fraction: retrieve matching point IDs from the payload index, then compute distances only for those points (indexed linear scan).
   - If no index exists for the filter field: fall back to full scan with inline filter evaluation.

4. **Segment results** are merged within the shard (top-k per shard).

5. **Shard results** are merged across shards, re-ranked, and the global top-k results are returned to the client with scores and optional payload/vector data.

### Design Decisions

**Rust over C++ or Go:** Qdrant chose Rust for its memory safety without garbage collection overhead. A vector database holds large amounts of data in memory (vector storage, HNSW graphs) and performs latency-sensitive operations. Rust's ownership model prevents memory leaks and data races at compile time, while its zero-cost abstractions and SIMD intrinsics deliver C-level performance. The absence of a garbage collector means no unpredictable pauses during search operations.

**Client-Server over Embedded:** Unlike DuckDB or SQLite, Qdrant runs as a server. This choice enables multi-client access, horizontal scaling via sharding and replication, and operational features like rolling upgrades and snapshot backups. The trade-off is network overhead per request, but for the typical use case (AI applications making API calls), this is negligible compared to the embedding model latency.

**HNSW over IVF or LSH:** Qdrant uses HNSW as its primary index because it provides the best combination of search quality (recall) and speed for general-purpose vector search. IVF (inverted file) indexes are faster to build but provide lower recall at the same query latency. LSH (locality-sensitive hashing) is simpler but less accurate. HNSW's graph structure also lends itself to filter-aware extensions -- Qdrant can skip non-matching nodes during traversal without pre-filtering, which is much harder with partition-based indexes like IVF.

**Segment-Based Storage over Append-Only Log:** The segment architecture (inspired by Lucene/Elasticsearch) separates write-optimized and read-optimized data paths. New writes go to a small, unindexed appendable segment for minimal write latency. The optimizer periodically "seals" these segments and builds HNSW indexes, creating immutable, search-optimized segments. This design avoids the tension between write performance and search performance that plagues single-structure databases.

**Custom Gridstore over RocksDB:** While Qdrant historically used RocksDB for some storage, it developed a custom storage engine called Gridstore optimized for vector workloads. Gridstore provides better control over memory layout, I/O patterns, and compression for the specific access patterns of vector data (sequential reads of fixed-size blocks during HNSW traversal).
