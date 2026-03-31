## Architecture
<!-- level: intermediate -->
<!-- references:
- [Qdrant System Architecture (DeepWiki)](https://deepwiki.com/qdrant/qdrant/2-system-architecture) | analysis
- [Distributed Deployment](https://qdrant.tech/documentation/operations/distributed_deployment/) | docs
- [Shards and Replica Sets (DeepWiki)](https://deepwiki.com/qdrant/qdrant/2.4-shards-and-replica-sets) | analysis
- [Introducing Gridstore](https://qdrant.tech/articles/gridstore-key-value-storage/) | blog
- [Qdrant Overview](https://qdrant.tech/documentation/overview/) | docs
-->

### High-Level Design

Qdrant is a multi-threaded, network-accessible vector database server written in Rust. In single-node mode it runs as a standalone process; in distributed mode it forms a symmetric peer-to-peer cluster where every node runs the full stack. The architecture is organized in four layers:

1. **API Layer** — REST (port 6333) and gRPC (port 6334) interfaces accepting client requests
2. **Table of Contents (TOC)** — The central storage orchestrator that manages all collections
3. **Shard Layer** — Horizontal partitioning via shards, each managed by a ReplicaSet
4. **Segment Layer** — The core storage units containing vector data, payload data, and indexes

### API Layer

Qdrant exposes two external API interfaces:

- **REST API** (port 6333) — OpenAPI 3.0 compliant, built on actix-web. Best for prototyping and debugging.
- **gRPC API** (port 6334) — High-performance binary protocol built with tonic. Recommended for production workloads due to lower serialization overhead.
- **Internal gRPC** (port 6335) — Used exclusively for cluster coordination: Raft consensus, shard transfers, health checks. Never exposed to clients.

Both REST and gRPC expose the same operations: collection management, point CRUD, search, recommendation, and cluster management.

### Table of Contents (TOC)

The TOC is the central orchestrator that sits between the API layer and the storage layer. It:

- Manages collection lifecycle (create, update, delete)
- Routes operations to the correct shard based on point ID or shard key
- Coordinates distributed operations across cluster nodes
- Manages collection aliases for zero-downtime migrations

### Shard Layer

Collections are horizontally partitioned into **shards** for scalability:

- **Auto sharding (default)** — Points are distributed across shards using a hash ring based on point ID. The number of shards is set at collection creation via `shard_number`.
- **Custom sharding** — Users define shard keys (e.g., tenant ID) for data locality control, enabling efficient multi-tenancy.

Each shard is managed by a **ReplicaSet** that coordinates between local and remote replicas:

- **Local replicas** reside on the current node and process reads/writes directly
- **Remote replicas** are proxied to other cluster nodes via internal gRPC

Replication factor determines how many copies of each shard exist across the cluster. With `replication_factor >= 2`, the system tolerates node failures without data loss.

### Segment Layer

Segments are the fundamental storage units within shards. Each segment stores a subset of points and independently maintains:

- **Vector storage** — The actual vector data (in-memory, memory-mapped, or quantized)
- **Payload storage** — JSON metadata indexed for filtering
- **Vector index** — HNSW graph for fast approximate nearest neighbor search
- **Payload index** — Inverted indexes and range indexes for filtered search
- **ID tracker** — Maps external point IDs to internal segment-local IDs

Segments transition through lifecycle states:

- **Appendable (Plain)** — Accepts new writes directly, no HNSW index. Fast writes, slow search.
- **Indexed (Immutable)** — HNSW index built, optimized for search. Created when segments reach size thresholds.
- **Proxy** — Temporary segments created during optimization to maintain read availability.

### Write-Ahead Log (WAL)

Every write operation is first persisted to the WAL before being applied to segments. This ensures durability — if the server crashes, operations can be replayed from the WAL on restart. Key WAL configuration:

- **Capacity per segment** — Controls WAL file sizes
- **Pre-allocated segments** — Reduces allocation overhead during writes
- **Retention policy** — Closed WAL segments are freed once their operations are confirmed applied to segments

In v1.17, Qdrant actively frees cache memory for closed WAL segments to reduce memory pressure.

### Optimizers (Async Workers)

Each local shard runs three asynchronous worker pools:

1. **Update Worker** — Applies point operations (upsert, delete, set_payload) from the WAL to appendable segments. Operations are ACKed immediately after WAL persistence.
2. **Optimize Worker** — Builds HNSW indexes, merges small segments into larger ones, vacuums deleted points. Runs continuously without blocking writes.
3. **Flush Worker** — Persists in-memory segment state to disk at configurable intervals (default: 5 seconds).

This separation ensures that expensive operations like HNSW index building never block write acknowledgment.

### Storage Engine: Gridstore

As of v1.17, Qdrant has fully replaced RocksDB with **Gridstore**, a custom-built key-value store designed specifically for vector database workloads. Gridstore provides:

- Lower tail latencies by reducing lock contention
- Better control over storage layout and I/O patterns
- Tighter integration with Qdrant's segment lifecycle
- Elimination of RocksDB compaction stalls

Direct upgrades from v1.15.x (RocksDB) to v1.17.x (Gridstore-only) are not supported; users must upgrade through v1.16.x first.

### Vector Storage Formats

Qdrant provides multiple vector storage backends optimized for different access patterns:

- **SimpleVectorStorage** — Full vectors in RAM (Vec). Fastest search, highest memory cost.
- **MmapVectorStorage** — Memory-mapped files for indexed segments. OS manages caching.
- **AppendableVectorStorage** — Chunked mmap enabling efficient appends for writable segments.
- **MultiDenseVectorStorage** — Multiple vectors per point for late-interaction models (ColBERT).

### Distributed Mode

When `cluster.enabled = true`, Qdrant forms a symmetric peer-to-peer cluster:

- **Raft Consensus** — Used for metadata operations: creating/deleting collections, shard transfers, configuration changes. One peer serves as Raft leader.
- **Direct Peer-to-Peer** — Data operations (upsert, delete, search) bypass Raft entirely. They go directly to the relevant shard replicas via internal gRPC on port 6335.
- **Clock Tags** — Data operations use vector clock-style tags for causal ordering without the overhead of full consensus.
- **Consistency Levels** — Clients can choose per-operation: `1` (fast, eventual), `majority`, `all` (strict, slower), or `quorum`.

This split design is crucial: metadata operations are rare and need strong consistency, while data operations are frequent and need low latency.

### Design Decisions

- **Rust over C++/Go/Java** — Memory safety without GC pauses, critical for predictable search latency
- **Symmetric cluster** — Every node runs the full stack, simplifying operations (no dedicated coordinator nodes)
- **WAL-first writes** — Durability guaranteed before acknowledgment, with async indexing
- **Segment-based storage** — Enables zero-copy optimization: new indexes are built on copies while the original segment serves reads
- **Custom storage (Gridstore)** — Purpose-built for vector workloads rather than relying on general-purpose key-value stores
