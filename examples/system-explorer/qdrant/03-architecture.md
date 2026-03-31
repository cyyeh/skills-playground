## Architecture
<!-- level: intermediate -->
<!-- references:
- [Built for Vector Search](https://qdrant.tech/articles/dedicated-vector-search/) | blog
- [Distributed Deployment](https://qdrant.tech/documentation/operations/distributed_deployment/) | official-docs
- [Qdrant High-Performance Vector Search Engine](https://qdrant.tech/qdrant-vector-database/) | official-docs
- [Exploring Distributed Vector Databases Performance on HPC Platforms](https://arxiv.org/html/2509.12384v1) | paper
-->

### High-Level Design

Qdrant follows a shared-nothing, peer-to-peer distributed architecture where each node is a full participant in the cluster -- there is no single master or dedicated coordinator node. The system is organized in concentric layers: the API layer accepts client requests via REST/gRPC, the collection layer manages logical data organization, the shard layer handles distribution across nodes, and the segment layer provides the actual storage and indexing engine.

```
                         ┌──────────────────────────────────┐
                         │          Client SDKs             │
                         │   (Python, JS, Rust, Go, Java)   │
                         └──────────────┬───────────────────┘
                                        │
                         ┌──────────────▼───────────────────┐
                         │        API Layer                  │
                         │   REST (port 6333)                │
                         │   gRPC (port 6334)                │
                         │   Web UI Dashboard                │
                         └──────────────┬───────────────────┘
                                        │
              ┌─────────────────────────▼──────────────────────────┐
              │               Collection Layer                      │
              │  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
              │  │ Collection A│  │ Collection B│  │Collection C│ │
              │  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘ │
              └─────────┼────────────────┼───────────────┼─────────┘
                        │                │               │
         ┌──────────────▼──────────────────────────────────────────┐
         │                    Shard Layer                            │
         │   ┌──────────┐ ┌──────────┐ ┌──────────┐               │
         │   │ Shard 0  │ │ Shard 1  │ │ Shard 2  │  (per node)   │
         │   │ Replica   │ │ Replica   │ │ Replica   │               │
         │   │ Set       │ │ Set       │ │ Set       │               │
         │   └────┬─────┘ └────┬─────┘ └────┬─────┘               │
         └────────┼────────────┼────────────┼──────────────────────┘
                  │            │            │
    ┌─────────────▼─────────────────────────▼──────────────────────┐
    │                    Segment Layer                               │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
    │  │   Mutable     │  │  Immutable    │  │  Immutable    │       │
    │  │   Segment     │  │  Segment      │  │  Segment      │       │
    │  │  (WAL-backed) │  │ (HNSW index) │  │ (HNSW index) │       │
    │  └──────────────┘  └──────────────┘  └──────────────┘       │
    │                                                               │
    │  Storage: Gridstore (custom) + mmap + optional disk offload  │
    └───────────────────────────────────────────────────────────────┘
```

### Key Components

**API Layer (REST + gRPC)** -- Provides the external interface for all client interactions. The REST API on port 6333 handles JSON-based requests and also serves the built-in web dashboard for cluster monitoring. The gRPC API on port 6334 provides higher-throughput binary communication, used by most client SDKs for production workloads. The API layer exists because Qdrant needs to serve diverse client ecosystems -- from quick prototyping with curl to high-throughput production pipelines -- without forcing a single protocol choice.

**Collection Manager** -- Orchestrates the lifecycle of collections: creation, configuration changes, deletion, and schema management. It resolves which shards and replicas own a given request and coordinates distributed operations. This component exists because collections are the user-facing boundary -- every operation is scoped to a collection, and the manager ensures configuration consistency across the cluster via [Raft consensus](https://qdrant.tech/documentation/operations/distributed_deployment/).

**Shard Holder & Replica Sets** -- Each collection is divided into shards, and each shard has a ShardReplicaSet that manages one or more replicas across nodes. The replica set handles read/write routing: reads prefer the local replica for latency, writes fan out to all replicas for durability. This component exists because horizontal scaling and fault tolerance require data partitioning (sharding) and redundancy (replication). Qdrant uses [consistent hashing](https://qdrant.tech/documentation/operations/distributed_deployment/) for automatic shard assignment, or user-defined shard keys for multi-tenant scenarios.

**Segment Holder & Optimizer** -- Within each shard, data lives in segments -- the fundamental storage and indexing units. The segment holder manages a mix of mutable segments (accepting writes) and immutable segments (fully indexed for search). A background [optimizer](https://qdrant.tech/articles/dedicated-vector-search/) monitors segment sizes and merges small segments, converts mutable segments to immutable with HNSW indexes, and compacts deleted data. This component exists because building an HNSW index is expensive (non-linear construction time), so Qdrant amortizes the cost by writing to lightweight mutable segments first and building full indexes in the background.

**HNSW Index Engine** -- The core approximate nearest neighbor (ANN) search implementation. Each immutable segment builds its own HNSW graph with configurable parameters (m, ef_construct, ef). The engine supports filterable HNSW -- integrating payload conditions directly into graph traversal -- and GPU-accelerated index construction. This component exists because brute-force vector comparison is O(n) per query, which is unacceptable at scale. HNSW provides O(log n) approximate search with tunable recall-latency trade-offs.

**Gridstore (Custom Storage Engine)** -- Qdrant's purpose-built storage engine optimized for fixed-size vector data. Unlike general-purpose key-value stores, Gridstore exploits the fact that all vectors in a collection have identical byte size, making offset calculation trivial and eliminating the overhead of variable-length record management. This component exists because vectors have a fundamentally different access pattern than typical database records -- fixed size, sequential scan-friendly, and amenable to memory-mapped I/O.

**Write-Ahead Log (WAL)** -- Ensures durability by persisting every write operation before it is applied to segments. On recovery, the WAL replays uncommitted operations to restore segment state. The WAL exists because crash recovery needs to be deterministic -- without it, a crash during a segment write could leave data in an inconsistent state.

**Raft Consensus Layer** -- Manages cluster-wide agreement on topology changes, collection metadata, and shard assignments. Qdrant uses Raft for structural operations (creating collections, moving shards, changing replica states) but deliberately excludes point-level operations from consensus to avoid the latency overhead. This design exists because cluster coordination needs strong consistency (you cannot have two nodes disagree on which collections exist), but point operations need speed and can tolerate eventual consistency between replicas.

### Data Flow

A vector search request flows through Qdrant in the following steps:

1. **Client sends request** -- A search query arrives via REST or gRPC, specifying the collection name, query vector, optional filters, and result limit.

2. **API layer routes to collection** -- The API handler validates the request, resolves the collection, and determines read consistency requirements (local, majority, quorum, or all).

3. **Collection fans out to shards** -- The collection manager identifies which shards need to participate. For unfiltered queries, all shards are queried. For queries with shard keys (multi-tenant), only matching shards participate.

4. **Shard replica selection** -- Each shard's ReplicaSet selects the best replica to query. Local replicas are preferred for latency. If read consistency requires multiple replicas, the request goes to the required number of peers.

5. **Segment-level search** -- Within each local shard, the SegmentsSearcher fans out the query across all segments concurrently using a thread pool. For each segment, the query planner decides the strategy: HNSW graph search (most queries), payload-index-only search (low-cardinality filters), or brute-force scan (very small segments).

6. **HNSW traversal with filtering** -- In the HNSW path, the search starts at the top layer's entry point and greedily descends through layers, scoring neighbors and following the best edges. If payload filters are active, the filterable HNSW conditions each traversal step on the payload index, skipping filtered-out nodes while maintaining graph connectivity.

7. **Quantized scoring (optional)** -- If quantization is enabled, initial scoring uses compressed vectors in RAM for speed. The top candidates are then re-scored against full-precision vectors (from disk or memory) for accuracy.

8. **Segment result merge** -- The BatchResultAggregator merges results from all segments within a shard, deduplicating by point ID and keeping the highest-scored entries per the requested limit.

9. **Cross-shard merge** -- Results from all shards are merged using k-way merge, respecting distance ordering. Payload and vector data are fetched if requested (using an optimization that defers payload transfer when the cost exceeds a threshold).

10. **Response to client** -- The final ranked list of ScoredPoints (IDs, scores, optional payloads and vectors) is serialized and returned to the client.

### Design Decisions

**Rust as the implementation language.** Qdrant chose Rust for memory safety without garbage collection pauses, predictable latency at the 99th percentile, and the ability to use unsafe SIMD intrinsics for distance calculations without risking memory corruption elsewhere. This decision means no GC stop-the-world pauses during search -- critical for latency-sensitive workloads -- but increases development velocity cost compared to Go or Java.

**Segments over monolithic indexes.** Rather than building one giant HNSW graph per collection (which would make updates extremely expensive), Qdrant splits data into segments with individual indexes. New data enters mutable segments (fast writes, scan-based search) and migrates to immutable segments (HNSW-indexed, fast search) via background optimization. This amortizes index build cost but means freshly inserted points have slightly higher search latency until optimization completes.

**Raft for metadata, not for points.** Point-level writes bypass Raft consensus and fan out directly to replicas. This gives Qdrant high write throughput (no consensus round-trip per point) at the cost of eventual consistency between replicas. Structural operations (collection creation, shard moves) go through Raft for strong consistency. This split exists because most vector workloads are write-heavy during ingestion and read-heavy during serving -- optimizing for both requires different consistency models.

**Filterable HNSW instead of pre/post-filtering.** Most vector databases either filter before search (breaking HNSW graph connectivity) or after search (wasting compute on irrelevant results). Qdrant integrates filtering into the HNSW traversal itself, conditioning graph navigation on payload indexes. When filters are too restrictive (low cardinality), the query planner automatically falls back to a payload-index-only search. This design avoids the pathological cases of both approaches but adds complexity to the index implementation.

**Custom storage engine over embedded databases.** Instead of using RocksDB or LevelDB (common choices for embedded storage), Qdrant built Gridstore -- a storage engine that exploits the fixed-size nature of vectors. Because every vector in a collection has identical byte size, storage locations can be calculated by simple arithmetic rather than B-tree lookups. This provides predictable low-latency access and efficient memory-mapped I/O, but means Qdrant maintains a larger codebase than systems that delegate to off-the-shelf storage.
