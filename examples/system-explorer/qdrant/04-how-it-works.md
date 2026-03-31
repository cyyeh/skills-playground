## How It Works
<!-- level: intermediate -->
<!-- references:
- [HNSW Indexing Fundamentals](https://qdrant.tech/course/essentials/day-2/what-is-hnsw/) | official-docs
- [Combining Vector Search and Filtering](https://qdrant.tech/course/essentials/day-2/filterable-hnsw/) | official-docs
- [What is Vector Quantization?](https://qdrant.tech/articles/what-is-vector-quantization/) | blog
- [A Complete Guide to Filtering in Vector Search](https://qdrant.tech/articles/vector-search-filtering/) | blog
- [Vector Search Resource Optimization Guide](https://qdrant.tech/articles/vector-search-resource-optimization/) | official-docs
-->

### HNSW Graph Construction and Search

The Hierarchical Navigable Small World algorithm is the heart of Qdrant's search performance. Understanding how it builds and traverses the graph reveals why Qdrant can find approximate nearest neighbors in logarithmic time.

**Graph Construction.** When an immutable segment is built, the HNSW constructor assigns each vector a random level using an exponential distribution controlled by a `level_factor` (derived from the `m` parameter). Most vectors land at level 0 (the densest layer); progressively fewer reach higher levels. Construction proceeds in two phases: a single-threaded bootstrap phase inserts the first batch of points (controlled by `SINGLE_THREADED_HNSW_BUILD_THRESHOLD`) to establish basic graph connectivity, then a parallel phase uses [Rayon](https://docs.rs/rayon/) thread pools to insert remaining points concurrently.

For each new point, the algorithm:
1. Starts at the current entry point and greedily descends through upper layers (beam width 1), finding the closest node at each level.
2. At the point's assigned level and below, it searches for `ef_construct` nearest neighbors.
3. It selects up to `m` neighbors to link using a heuristic that rejects candidates whose distance to already-selected neighbors is less than their distance to the new point -- preventing redundant short-range links and promoting graph diversity.
4. Bidirectional links are established: the new point links to its neighbors, and those neighbors add back-links to the new point (pruning if they exceed `m` or `m0` connections).

**Graph Search.** A search query follows a similar top-down traversal:
1. Enter at the highest layer's entry point.
2. At each layer above the base, greedily walk toward the query vector (beam width 1), moving to whichever neighbor is closest to the query.
3. At the base layer (level 0), expand the search with beam width `ef` (the search-time parameter), maintaining a priority queue of candidates and a visited set.
4. Return the top-k closest points from the priority queue.

The key parameters that control quality and speed:
- **`m`** (default 16): Maximum edges per node at non-zero levels. Higher values improve recall but increase memory and build time.
- **`m0`** (typically 2*m = 32): Maximum edges per node at level 0. The base layer is denser because it is where final results are found.
- **`ef_construct`** (default 100): Search width during construction. Higher values build better graphs but take longer.
- **`ef`** (search-time parameter): Search width during queries. Higher values improve recall at the cost of latency.

### Filterable HNSW

Standard HNSW assumes all points are candidates. When payload filters restrict the search space, naive approaches break down: pre-filtering removes points from the graph, destroying connectivity and trapping the search in disconnected components; post-filtering wastes compute scoring irrelevant points.

Qdrant solves this with [filterable HNSW](https://qdrant.tech/course/essentials/day-2/filterable-hnsw/), which integrates filtering directly into graph traversal:

1. **Payload indexes** are maintained alongside the HNSW graph. These are inverted indexes mapping payload field values to point IDs -- similar to indexes in a traditional document database.
2. During HNSW traversal, each candidate node is checked against the filter condition using the payload index. Filtered-out nodes are skipped but their graph links are still traversed -- the algorithm uses them as "stepping stones" to reach qualifying nodes.
3. The HNSW graph itself is conditioned on possible filtering dimensions during construction: additional links are built to maintain connectivity for common filter patterns.

**Adaptive Query Planning.** Qdrant's query planner estimates the cardinality of a filter (how many points it matches) and selects the optimal strategy:
- **High cardinality** (filter matches most points): Use standard HNSW with in-traversal filtering.
- **Medium cardinality**: Use HNSW with aggressive filtering and expanded ef to compensate for reduced graph connectivity.
- **Low cardinality** (filter matches very few points, below `full_scan_threshold`): Skip HNSW entirely. Use the payload index to enumerate matching points and brute-force score them. This is faster when the candidate set is small enough.

This adaptive approach means Qdrant avoids the pathological cases of both pre-filtering and post-filtering, though it requires maintaining both HNSW and payload indexes simultaneously.

### Segment Lifecycle and Optimization

Qdrant's segment architecture is a key differentiator -- it allows concurrent reads, writes, and index building without global locks.

**Mutable Segments** accept new points immediately. They use a simple scan-based search (no HNSW graph), which is fast for small segment sizes but degrades linearly as the segment grows. Writes are backed by a Write-Ahead Log (WAL) for durability.

**Immutable Segments** are created when the optimizer converts a mutable segment. The optimizer:
1. Takes a snapshot of the mutable segment's data.
2. Builds an HNSW index on the snapshot (potentially GPU-accelerated).
3. Applies any quantization (scalar, product, or binary).
4. Atomically swaps the new immutable segment in, replacing the old mutable segment.
5. Search operations seamlessly transition -- queries that were scanning the mutable segment now traverse the HNSW graph of the immutable segment.

**Merge Optimization** periodically combines small immutable segments into larger ones, reducing the number of segments that must be searched per query. The optimizer balances segment count (fewer is better for search) against segment size (smaller is better for index build time).

**Deletion Handling.** Deleted points are marked with a tombstone rather than physically removed. When tombstone density exceeds a threshold, the optimizer compacts the segment, physically removing deleted data and rebuilding the index. This avoids the cost of modifying HNSW graphs in-place (which would require expensive relinking).

### Quantization Engine

Qdrant implements three quantization strategies, each trading accuracy for memory and speed differently:

**[Scalar Quantization](https://qdrant.tech/articles/scalar-quantization/)** maps each float32 dimension (4 bytes) to an int8 value (1 byte), achieving 4x compression. The mapping learns the range [min, max] for each dimension and linearly scales values to [0, 255]. Distance calculations on int8 values leverage SIMD instructions for ~2x additional speedup beyond the memory savings.

**[Product Quantization](https://qdrant.tech/articles/product-quantization/)** divides each vector into sub-vectors (e.g., a 768-dimensional vector into 96 sub-vectors of 8 dimensions each), then clusters each sub-vector space into 256 centroids using k-means. Each sub-vector is replaced by its 1-byte centroid ID, achieving compression ratios from 4x to 64x. Distance computation uses pre-computed lookup tables. The trade-off: product quantization is not SIMD-friendly, so while it compresses more aggressively than scalar, individual distance calculations are slower.

**[Binary Quantization](https://qdrant.tech/articles/binary-quantization/)** reduces each dimension to a single bit (positive or negative), achieving 32x compression. Distance computation becomes a bitwise XOR followed by a popcount -- native CPU operations that deliver up to 40x speed improvement over float32. Binary quantization works best with high-dimensional vectors from models like OpenAI's Ada-002 (1536 dimensions) or Cohere's embeddings, where the information loss per dimension is offset by the sheer number of dimensions.

**Oversampling and Re-scoring.** All quantization methods use a two-phase approach: the quantized vectors produce a fast, approximate ranking, then the top candidates (oversampled by a configurable factor) are re-scored against the full-precision vectors for final ranking. This recovers most of the accuracy lost during quantization.

### Distributed Consensus and Replication

In distributed mode, Qdrant uses the [Raft consensus protocol](https://qdrant.tech/documentation/operations/distributed_deployment/) with a critical optimization: consensus governs cluster structure only, not individual data operations.

**What Raft controls:**
- Cluster membership (which peers are alive)
- Collection metadata (schemas, configurations)
- Shard assignments (which shard replicas live on which peers)
- Replica state transitions (Active, Dead, Initializing, etc.)

**What Raft does NOT control:**
- Individual point upserts, deletes, and updates
- Search queries

Point-level writes are forwarded directly from the receiving node to all replicas in the shard's ReplicaSet. The `write_consistency_factor` controls how many replicas must acknowledge before the client gets a response (default 1, configurable up to all replicas). This gives Qdrant much higher write throughput than a system that consensus-replicates every point.

**Shard Transfer Methods:**
- `stream_records`: Streams point data record by record; the receiving node rebuilds indexes from scratch. Simplest and most robust.
- `snapshot`: Transfers the entire segment state (data + indexes) as a snapshot. Faster for large shards because the receiving node does not need to rebuild the HNSW index.
- `wal_delta`: Transfers only the WAL entries that differ between replicas. Fastest for recovering a replica that has been temporarily offline. Falls back to `stream_records` if the WAL gap is too large.

### Performance Characteristics

**Search latency:** Sub-20ms query latency at p50 for billion-scale datasets with quantization enabled, as reported in [Qdrant benchmarks](https://qdrant.tech/qdrant-vector-database/). Latency scales logarithmically with dataset size thanks to HNSW, but linearly with the number of segments searched per query.

**Indexing throughput:** GPU-accelerated HNSW construction achieves up to 10x faster ingestion compared to CPU-only builds. Incremental HNSW indexing (added in 2025) further reduces overhead for upsert-heavy workloads by updating existing graph structures rather than rebuilding from scratch.

**Memory efficiency:** With binary quantization on 1536-dimensional vectors, memory usage drops from ~6 KB per vector to ~192 bytes -- enabling a billion vectors to fit in approximately 180 GB of RAM (quantized) versus 5.7 TB (uncompressed). The optimal production pattern puts original vectors on disk (`on_disk: true`) and quantized vectors in RAM (`always_ram: true`).

**Filtered search overhead:** Payload-filtered searches add 10-30% latency compared to unfiltered searches when the filter matches >50% of points. For very restrictive filters (<1% match), the payload-index-only path can be faster than HNSW because it avoids graph traversal entirely.

**Write throughput:** Single-node write throughput depends on vector dimensionality and payload size, but typical production deployments sustain 10,000-50,000 points/second for 768-dimensional vectors with moderate payloads.
