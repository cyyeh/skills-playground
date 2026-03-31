## Architecture
<!-- level: intermediate -->
<!-- references:
- [Qdrant System Architecture (DeepWiki)](https://deepwiki.com/qdrant/qdrant/2-system-architecture) | wiki
- [Qdrant Storage Documentation](https://qdrant.tech/documentation/manage-data/storage/) | official-docs
- [Qdrant Distributed Deployment](https://qdrant.tech/documentation/operations/distributed_deployment/) | official-docs
- [Shards and Replica Sets (DeepWiki)](https://deepwiki.com/qdrant/qdrant/2.4-shards-and-replica-sets) | wiki
-->

### Component Overview

Qdrant employs a seven-layer architecture that progresses from external client interactions down to disk persistence:

```
Client SDKs & Frameworks (Python, JS, Rust, Go, Java, .NET)
        |
   API Layer (REST on port 6333 / gRPC on port 6334)
        |
   Application Core (Dispatcher + ConsensusManager)
        |
   Collection Management (TableOfContent + Collection)
        |
   Shard Layer (LocalShard / RemoteShard)
        |
   Storage Layer (Segments: vectors + payloads + indexes)
        |
   Persistence (WAL + GridStore/RocksDB + mmap files)
```

### API Layer

The API layer handles protocol conversion and request routing. REST is served by actix-web on port 6333, providing a JSON-based interface suitable for prototyping and general use. gRPC is served by tonic on port 6334, offering a binary protocol optimized for high-throughput production workloads. Both protocols expose identical functionality — every REST endpoint has a corresponding gRPC method. An internal gRPC channel on port 6335 handles peer-to-peer communication in distributed mode.

### Application Core

The Dispatcher sits at the center of request routing, directing incoming operations to the appropriate collection and shard. In distributed mode, the ConsensusManager coordinates cluster-wide state changes using the Raft protocol. Metadata operations (collection creation, deletion, shard transfers) flow through Raft consensus, while data operations (upserts, searches) bypass consensus for performance and use direct peer-to-peer communication.

### Collection Management

The TableOfContent is the top-level registry that tracks all collections in the system. Each Collection manages its own sharding configuration, replication settings, and optimizer parameters. A collection is the primary organizational boundary — all points within a collection share the same vector configuration.

### Shard Layer

Collections are divided into shards, each representing a self-contained store of points. A LocalShard owns actual data, containing segments and a WAL. A RemoteShard is a proxy that forwards requests to a shard hosted on another peer via internal gRPC. Shards are managed by ReplicaSets, which maintain multiple replicas across different peers for fault tolerance. Replica states include Active (fully synced), Dead (failed), Partial (recovering), Initializing (being created), and Listener (read-only backup).

### Storage Engine and Segments

Data within each shard is organized into segments — the fundamental unit of storage and indexing. Each segment is self-contained with its own vector storage, payload storage, HNSW index, payload field indexes, and ID mapper.

Segments transition through states:
- **Plain (appendable):** Mutable segments that accept new writes. They use simple vector storage without an HNSW index, relying on brute-force search. Every shard maintains at least one appendable segment for incoming data.
- **Indexed (non-appendable):** Immutable segments with a built HNSW index and optimized storage. Created by the optimizer when a segment reaches the indexing threshold (default: 10,000 points).
- **Special (temporary):** Proxy and copy-on-write segments created during optimization operations to handle concurrent reads and writes safely.

### Vector Storage Options

Qdrant offers two vector storage backends:

- **In-Memory Storage:** All vectors are held in RAM for maximum speed. Disk is only used for persistence. Ideal for smaller collections or when latency is the top priority.
- **Memmap Storage:** Vectors are stored in memory-mapped files. The operating system's page cache manages which portions are in RAM. With sufficient memory, performance approaches in-memory storage; with less memory, it gracefully degrades by paging to disk. Configured via `on_disk: true` at collection creation or the `memmap_threshold` parameter.

### Payload Storage

- **InMemory Payload Storage:** Payload data is loaded into RAM at startup. Fast reads but higher memory usage, especially with large payloads.
- **OnDisk Payload Storage:** Payload data is read directly from the storage backend (RocksDB or GridStore). Lower memory usage at the cost of increased read latency. Field indexes for frequently-filtered fields remain in RAM regardless of storage type.

### Write-Ahead Log (WAL)

The WAL ensures durability and crash recovery. All write operations follow a two-stage process: first written to the WAL (ordered and sequentially numbered), then applied to segments. Each segment tracks the version number of each point; during recovery, operations with version numbers lower than the current point version are safely skipped, preventing duplicate application. Key configuration parameters include `wal_capacity_mb` (size per WAL segment), `wal_segments_ahead` (pre-allocated segment buffers), and `wal_retain_closed` (number of retained closed segments).

### Optimizer Pipeline

The optimizer coordinates three asynchronous worker pools:

1. **Update Worker:** Applies point operations (upsert, delete, set payload) to segments immediately after WAL persistence. Runs on every write.
2. **Optimize Worker:** Builds HNSW indexes when segments reach size thresholds, merges small segments, and vacuums deleted points. This is the process that converts plain segments into indexed segments.
3. **Flush Worker:** Periodically persists segment state to disk (default interval: 5 seconds via `flush_interval_sec`).

All three workers communicate asynchronously via channels, preventing expensive indexing operations from blocking client requests.

### Distributed Architecture

In distributed mode, Qdrant forms a cluster of peers that communicate using Raft consensus for metadata operations and direct gRPC for data operations.

**Sharding:** Collections are split into shards distributed across peers. Automatic sharding uses consistent hashing to distribute points evenly. Custom sharding (v1.7.0+) allows explicit shard assignment per point, useful for multi-tenant architectures.

**Replication:** Each shard can have multiple replicas across different peers (configured via `replication_factor`). Write operations are forwarded to all replicas with configurable write consistency (how many replicas must acknowledge before responding).

**Consensus:** Raft consensus ensures all peers agree on cluster topology and collection structure. An odd number of nodes (3, 5, 7) is recommended for reliable leader election. Point-level operations bypass Raft for performance, using clock tags for causal ordering instead.

**Shard Transfer Methods:**
- `stream_records` (v0.8.0+): Streams point data to the target, which rebuilds indexes locally. Weak ordering.
- `snapshot` (v1.7.0+): Transfers a full snapshot including indexes. Strong ordering.
- `wal_delta` (v1.8.0+): Transfers only the WAL delta for incremental sync. Strong ordering.
