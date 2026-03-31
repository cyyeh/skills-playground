## How It Works
<!-- level: intermediate -->
<!-- references:
- [HNSW Indexing Fundamentals](https://qdrant.tech/course/essentials/day-2/what-is-hnsw/) | course
- [Filterable HNSW](https://qdrant.tech/articles/filtrable-hnsw/) | blog
- [Combining Vector Search and Filtering](https://qdrant.tech/course/essentials/day-2/filterable-hnsw/) | course
- [HNSW Index Implementation (DeepWiki)](https://deepwiki.com/qdrant/qdrant/3.2-payload-indexing-and-filtering) | analysis
- [Vector Search Resource Optimization Guide](https://qdrant.tech/articles/vector-search-resource-optimization/) | blog
- [Hybrid Search with Query API](https://qdrant.tech/articles/hybrid-search/) | blog
-->

### The HNSW Search Algorithm

HNSW (Hierarchical Navigable Small World) is the heart of Qdrant's search engine. Understanding how it works reveals why vector search can be so fast.

#### Building the Graph

When vectors are indexed, HNSW constructs a multi-layered graph:

1. **Layer assignment** — Each new vector is randomly assigned a maximum layer using an exponential decay function. Most vectors exist only on layer 0 (the bottom); a few reach higher layers.
2. **Connection phase** — Starting from the top layer's entry point, the algorithm greedily navigates to the nearest neighbors of the new vector, then creates bidirectional edges. This repeats at each layer down to layer 0.
3. **Edge pruning** — Each node maintains at most `m` connections per layer (configurable, typically 16-64). The `ef_construct` parameter controls how many candidates are evaluated during construction — higher values produce a better-connected graph at the cost of slower builds.

The result is a navigable graph where high layers provide "express lanes" (few nodes, long-distance connections) and low layers provide "local streets" (many nodes, fine-grained connections).

#### Searching the Graph

Given a query vector, HNSW search proceeds:

1. **Enter at the top** — Start at the graph's entry point on the highest layer.
2. **Greedy descent** — At each layer, greedily navigate to the node closest to the query vector. This uses the "express lanes" to quickly reach the right neighborhood.
3. **Expand at the bottom** — On layer 0, perform a beam search with `ef` candidates (configurable at query time). This explores the local neighborhood thoroughly to find the best matches.
4. **Return top-k** — Sort candidates by distance and return the requested number of nearest neighbors.

The key insight: higher layers have exponentially fewer nodes, so the greedy descent is O(log N). The expensive detailed search only happens in the local neighborhood at the bottom layer.

### Filterable HNSW: Qdrant's Key Innovation

Standard HNSW has a fundamental problem with filters: if you search the graph and then filter results, you may discard most matches and return poor-quality results. If you filter first and then search, the graph may become disconnected (many nodes removed), causing the search to miss entire regions.

Qdrant solves this with **filterable HNSW**:

1. **Payload-aware edges** — During index construction, Qdrant builds additional edges between nodes that share common payload values. For each indexed payload field value, a subgraph of matching nodes is constructed, and extra edges are added to ensure these subgraphs remain navigable.
2. **Filter-during-search** — During search, the HNSW traversal checks each candidate against the filter condition. Non-matching candidates are skipped but still used for navigation (they help traverse the graph). Only matching candidates are added to the result set.
3. **Adaptive strategy** — Qdrant automatically chooses the best search strategy based on the estimated filter selectivity:
   - **Low selectivity (broad filter)** — Uses the standard HNSW graph with filter checks
   - **Medium selectivity** — Uses filterable HNSW with extra edges
   - **High selectivity (narrow filter)** — Falls back to filtered scan of the payload index, then rescores candidates

This adaptive approach ensures good performance regardless of how selective the filter is.

### ACORN Algorithm

For queries with multiple high-cardinality filters, Qdrant implements the **ACORN** (Approximate Computation of k-nearest neighbors Over Realistic datasets with Noise) algorithm. ACORN improves search accuracy when filters combine multiple conditions that individually match many points but together match few — a scenario where standard filterable HNSW can struggle.

### Scoring and Distance Metrics

Qdrant supports four distance metrics for measuring vector similarity:

- **Cosine** — Measures the angle between vectors (normalized dot product). Most common for text embeddings. Range: -1 to 1.
- **Dot Product** — Raw inner product. Useful when vector magnitude carries meaning. Range: unbounded.
- **Euclidean (L2)** — Straight-line distance in vector space. Lower is more similar. Range: 0 to infinity.
- **Manhattan (L1)** — Sum of absolute differences. Less sensitive to outlier dimensions. Range: 0 to infinity.

The distance metric is set per collection (or per named vector) at creation time. It affects both index construction and search. Internally, Qdrant uses SIMD-optimized distance functions for maximum throughput.

### The Indexing Pipeline

When you upsert points into Qdrant, they flow through a multi-stage pipeline:

1. **WAL persistence** — The operation is written to the write-ahead log. The client receives an acknowledgment.
2. **Appendable segment** — The point is added to a writable segment with no HNSW index (plain storage). This ensures fast write ingestion.
3. **Threshold detection** — The optimize worker monitors segment sizes. When an appendable segment exceeds the configured threshold, optimization is triggered.
4. **Segment optimization** — A new indexed segment is built:
   - Vector data is organized into the chosen storage format (mmap or in-memory)
   - HNSW index is constructed with the configured `m` and `ef_construct` parameters
   - Payload indexes are built for indexed fields
5. **Segment swap** — The new indexed segment atomically replaces the old appendable segment. Reads switch seamlessly via a proxy segment during the transition.
6. **WAL cleanup** — Once all operations in a WAL segment have been applied and the segment is indexed, the WAL segment is freed.

### Segment Lifecycle

Segments go through distinct phases:

```
[New writes] --> Appendable Segment (no HNSW, fast writes)
                      |
                 [Size threshold reached]
                      |
                      v
              Optimization (build HNSW, build payload indexes)
                      |
                      v
              Indexed Segment (HNSW graph, fast search)
                      |
                 [Many deletes accumulated]
                      |
                      v
              Vacuum/Merge (compact, rebuild index)
```

Multiple small indexed segments may also be merged into larger ones to reduce the number of segments that must be searched per query.

### Hybrid Search Pipeline

Qdrant's Query API enables combining multiple search strategies in a single request:

1. **Dense search** — Semantic similarity using dense vector embeddings
2. **Sparse search** — Lexical matching using sparse vectors (BM25, SPLADE)
3. **Fusion** — Results from multiple searches are combined using Reciprocal Rank Fusion (RRF) or Distribution-Based Score Fusion (DBSF)
4. **Re-ranking** — Optional re-scoring using a separate model or multivector (ColBERT) scoring
5. **Return** — Final ranked results with scores and payloads

The entire fusion and re-ranking pipeline runs server-side, eliminating multiple round-trips between client and server.

### Quantized Search

When quantization is enabled, the search pipeline adds an optimization step:

1. **Coarse search** — HNSW traversal uses quantized vectors for fast distance approximation. This quickly narrows candidates from millions to a few hundred.
2. **Rescoring** — Top candidates are rescored using the original full-precision vectors for accurate final ranking.
3. **Oversampling** — To compensate for quantization error, more candidates than requested are retrieved in the coarse phase. The `oversampling` parameter (e.g., 2.0) controls how many extra candidates are evaluated.

This two-phase approach provides most of the memory savings of quantization with minimal accuracy loss.
