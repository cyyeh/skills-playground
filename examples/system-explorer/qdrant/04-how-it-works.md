## How It Works
<!-- level: intermediate -->
<!-- references:
- [HNSW Indexing Fundamentals - Qdrant Course](https://qdrant.tech/course/essentials/day-2/what-is-hnsw/) | official-docs
- [Filtrable HNSW - Qdrant](https://qdrant.tech/articles/filtrable-hnsw/) | blog
- [Vector Search Resource Optimization Guide - Qdrant](https://qdrant.tech/articles/vector-search-resource-optimization/) | official-docs
- [Qdrant 1.15 - Smarter Quantization](https://qdrant.tech/blog/qdrant-1.15.x/) | blog
- [Qdrant 1.16 - ACORN Filtered Search](https://qdrant.tech/blog/qdrant-1.16.x/) | blog
-->

### HNSW Graph Construction

Qdrant builds an HNSW (Hierarchical Navigable Small World) graph for each segment's vector data. The graph is a multi-layered structure where layer 0 contains all points and each successive layer contains an exponentially decreasing random subset of points. The layering follows a logarithmic distribution: a point's maximum layer is determined by `-ln(rand()) * (1/ln(m))`, where `m` is the connectivity parameter.

During construction, each new point is inserted by:

1. **Finding the entry point** at the topmost layer and performing a greedy search downward (beam size = 1) to find the closest point at each layer.
2. **At each layer from the point's assigned level down to 0**, performing a beam search (width = `ef_construct`) to find the closest `ef_construct` neighbors.
3. **Selecting `m` neighbors** from the candidates using a heuristic that balances proximity and diversity (preferring neighbors that are not too close to each other, ensuring good graph connectivity).
4. **Adding bidirectional edges** between the new point and its selected neighbors. If any neighbor exceeds its maximum connection count (`m` at upper layers, `m * 2` at layer 0), its weakest connections are pruned.

The key parameters are:
- `m` (default 16): Maximum connections per node per layer. Higher = better recall, more memory. Each connection stores a neighbor ID (and optionally a quantized vector in compressed format).
- `ef_construct` (default 100): Search width during construction. Higher = better graph quality, slower indexing.
- Layer 0 has `m0 = m * 2` connections because it's the most-traversed layer and benefits most from higher connectivity.

Qdrant can build the main HNSW graph on GPU when available, significantly accelerating construction for large collections.

### HNSW Search Algorithm

Searching the graph follows a top-down, greedy-to-beam approach:

1. **Enter at the top layer** via the stored entry point (the highest-level node).
2. **Greedy descent** (layers L_max down to 1): At each layer, perform a greedy search with beam size 1, moving to the neighbor closest to the query vector. This quickly navigates to the right "neighborhood" with minimal computation.
3. **Beam search at layer 0**: Using the closest point found during descent as the starting point, perform a full beam search with width `ef` (the query-time parameter, called `hnsw_ef` in the API). Maintain a priority queue of candidates and a result set. Expand the closest unvisited candidate by scoring all its neighbors, adding better-than-worst candidates to both queues. Stop when the best remaining candidate is worse than the worst result.
4. **Return top-k** results from the beam search result set.

The `hnsw_ef` parameter (default 128) controls the recall-latency trade-off at query time. Higher values mean the search explores more nodes, finding better results at the cost of more distance computations. Setting `exact: true` in search parameters bypasses HNSW entirely and performs a brute-force scan for perfect recall.

### Filterable HNSW

Standard HNSW has a critical problem with filtered search: if you filter out 90% of points, the graph becomes disconnected -- the search can't reach matching points because the path goes through filtered-out nodes. Qdrant solves this with a multi-strategy approach:

**Filter-Aware Graph Construction:** When building the HNSW graph, Qdrant creates additional edges specifically for indexed payload values. For a field like `brand`, it builds sub-graphs for each value ("Apple", "Samsung", etc.) and merges them back into the main graph. This ensures that even under strict filtering, the graph remains connected for common filter values.

**Query-Time Strategy Selection:** Qdrant's query planner dynamically selects the best search strategy per segment based on the filter's estimated selectivity:

1. **Large result set (filter matches > threshold):** Use standard HNSW traversal but skip non-matching nodes during beam search. The graph is connected enough that traversal finds matching points efficiently. This is the most common case.

2. **Medium result set:** Use HNSW with extended `ef` to compensate for the nodes skipped by filtering, ensuring adequate recall.

3. **Small result set (highly selective filter):** Retrieve the matching point IDs directly from the payload index, then compute exact distances only for those points. This is essentially an indexed linear scan -- faster than HNSW when the filter is very selective because there are few distances to compute.

4. **No applicable index:** Fall back to full scan with inline filter evaluation on each point's payload.

The ACORN algorithm (introduced in v1.16) further improves filtered search by performing two-hop exploration during traversal -- when a neighbor doesn't match the filter, ACORN checks that neighbor's neighbors, potentially finding matching points that would otherwise require many more traversal steps.

### Quantization

Quantization reduces the memory footprint of vectors by compressing them from 32-bit floats to lower-precision representations. Qdrant supports three quantization methods:

**Scalar Quantization (SQ):** Compresses each float dimension to an 8-bit integer (int8). The range of values in each dimension is mapped linearly to [0, 255]. This reduces memory by 4x with minimal accuracy loss (typically < 1% recall drop). Scalar quantization is the safest default -- it works well for virtually all embedding models.

**Product Quantization (PQ):** Divides the vector into sub-vectors (segments) and quantizes each sub-vector independently using a learned codebook. This can achieve 8-32x compression but with larger accuracy trade-offs. PQ works best with higher-dimensional vectors (768+) where the redundancy between dimensions can be exploited.

**Binary Quantization (BQ):** The most aggressive compression -- each float dimension is reduced to a single bit (positive = 1, negative = 0). This achieves 32x memory reduction and enables extremely fast Hamming distance computation. However, BQ only works well with specific embedding models that produce binary-friendly distributions (e.g., OpenAI's `text-embedding-3-large` and Cohere's `embed-v3`). For incompatible models, BQ causes significant accuracy loss.

**Asymmetric Quantization** (introduced in v1.15): Allows the query vector to remain unquantized while database vectors are quantized. Distance computations use the full-precision query against quantized stored vectors, improving accuracy without increasing memory usage. This is the default behavior when quantization is enabled.

**Rescoring:** When using quantization, Qdrant performs a two-stage search: first, it uses quantized vectors for fast approximate scoring to find candidate points, then it rescores the top candidates using the original full-precision vectors for final ranking. The `rescore` parameter (default: true) and `oversampling` factor (how many extra candidates to retrieve for rescoring) control this process.

### Storage Engine

**Vector Storage:** Qdrant stores vectors in one of several formats: in-memory (fastest, most RAM), memory-mapped files (mmap -- uses OS page cache, allows datasets larger than RAM), and chunked mmap (optimized for large segments). The storage format is configured per-collection and affects the memory/performance trade-off.

**Payload Storage:** Payloads are stored as JSON objects using either RocksDB-backed storage (default), memory-mapped storage, or in-memory storage. The choice depends on the workload: RocksDB provides good general-purpose performance, mmap provides predictable latency, and in-memory provides the fastest access for small datasets.

**Payload Indexing:** Qdrant maintains a `StructPayloadIndex` that builds efficient indexes on payload fields. Supported index types include:
- **Keyword index** for exact string matching
- **Full-text index** with tokenization for text search
- **Integer/Float index** for range queries
- **Geo index** for spatial queries (bounding box, radius, polygon)
- **Datetime index** for temporal queries
- **UUID index** for fast ID-based lookups
- **Bool index** for boolean filtering

The index decision (which type, when to build) is explicit -- you create a payload index on a field via API call, and Qdrant builds the appropriate index structure.

**Write-Ahead Log:** Every mutation (upsert, delete, set payload) is first written to the per-shard WAL. The WAL uses a sequential append format for fast writes. On startup, the shard replays any WAL entries that weren't yet flushed to segments, ensuring crash recovery.

### Distributed Operations

In distributed mode (multiple Qdrant nodes forming a cluster):

**Sharding** divides a collection's data across nodes. Each shard holds a subset of points determined by consistent hashing on point IDs. You can configure the number of shards at collection creation time. Searches broadcast to all shards, while point operations route to the specific shard owning that point ID.

**Replication** creates copies of each shard on multiple nodes. The replication factor (default: 1, meaning no replication) controls fault tolerance. Write operations propagate to all replicas (with configurable consistency: `majority`, `all`, or `quorum`). Read operations can target any replica, with an optional `read_fan_out_delay` that queries additional replicas if the first doesn't respond quickly enough.

**Consensus:** Cluster metadata (which collections exist, which shards are on which nodes, replica states) is managed via Raft consensus. This ensures all nodes agree on cluster topology even during network partitions. Data operations bypass Raft for performance -- they use direct peer-to-peer gRPC calls.

### Performance Characteristics

**Where it's fast:**
- Similarity search with filtering: Qdrant's filterable HNSW and query planner deliver sub-millisecond p99 latency for typical workloads (1M vectors, 768 dimensions). With quantization, it handles 100M+ vectors on a single node.
- Complex multi-condition filters: The payload indexing system evaluates compound filters (AND/OR/NOT with nested conditions) efficiently by intersecting posting lists from individual field indexes.
- High-throughput ingestion: Batch upserts with WAL-based durability handle tens of thousands of points per second per node.

**Where it's slower:**
- Cold starts with mmap storage: The first queries after startup may be slow as the OS page cache warms up. Use `on_disk: false` for latency-sensitive workloads that need consistent performance from the first query.
- Very high-dimensional vectors (4096+): Distance computation cost scales linearly with dimensionality. Quantization becomes increasingly important at higher dimensions.
- Cross-shard searches with strict ordering: Distributed searches must gather results from all shards and merge them, adding network latency proportional to the number of shards and the slowest shard.
