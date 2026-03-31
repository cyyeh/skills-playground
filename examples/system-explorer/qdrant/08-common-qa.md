## Common Q&A
<!-- level: all -->
<!-- references:
- [Qdrant FAQ](https://qdrant.tech/documentation/faq/) | official-docs
- [Qdrant Performance Tuning](https://qdrant.tech/documentation/guides/optimize/) | official-docs
- [Vector Search Resource Optimization Guide](https://qdrant.tech/articles/vector-search-resource-optimization/) | official-docs
-->

### Q: How much RAM does Qdrant need for my dataset?

The RAM formula depends on your storage configuration:

**Vectors in RAM (default):** `N * D * 4` bytes for float32 vectors, where N = number of points and D = dimensionality. For 1M vectors at 1536 dimensions: ~5.7 GB for vectors alone.

**HNSW graph:** `N * m * 2 * 8` bytes approximately (layer 0 links). For 1M vectors with m=16: ~256 MB for the graph.

**Payloads:** Varies by content size. Typically 100-500 bytes per point for typical metadata.

**With scalar quantization (int8):** Vector RAM drops to `N * D * 1` bytes -- a 4x reduction. For 1M vectors at 1536d: ~1.4 GB instead of 5.7 GB.

**With mmap (on_disk=true):** Vectors and/or HNSW graph are memory-mapped from disk. RAM usage depends on OS page cache behavior and access patterns. You need enough RAM to keep the "hot" portion of data cached, but the full dataset can exceed available RAM.

**Practical guideline:** For a production deployment with scalar quantization and always_ram=true for quantized vectors: budget ~2 bytes per dimension per point for combined vector + index RAM. For 10M points at 768 dimensions: ~15 GB RAM.

### Q: How do I choose between Cosine, Euclidean, and Dot Product distance?

**Cosine similarity** measures the angle between vectors, ignoring magnitude. Use it when your embedding model produces vectors with varying lengths but where direction encodes meaning. Most text embedding models (OpenAI, sentence-transformers) work best with Cosine. Qdrant optimizes Cosine by pre-normalizing vectors at insert time, making Cosine search as fast as Dot Product.

**Dot Product** measures both direction and magnitude similarity. Use it when vector magnitude carries meaning (e.g., popularity-weighted embeddings). If your vectors are already L2-normalized, Dot Product and Cosine produce identical results.

**Euclidean (L2) distance** measures straight-line distance in vector space. Use it for geometric applications or when your embedding model documentation specifically recommends L2 distance.

**Manhattan (L1) distance** is the sum of absolute differences. Rarely used in practice for embeddings but useful for specific applications like comparing histograms.

**When in doubt, use Cosine.** It's the most universally compatible choice and Qdrant's pre-normalization optimization makes it computationally equivalent to Dot Product.

### Q: When should I enable quantization, and which type?

**Scalar quantization (int8):** Enable it when RAM is your bottleneck. It provides 4x memory reduction with typically less than 1% recall loss. This is the safest choice and works with virtually all embedding models. Enable `always_ram=true` to keep quantized vectors in RAM while original vectors stay on disk -- this gives you the memory savings of quantization with original-precision rescoring.

**Binary quantization:** Enable it only with compatible embedding models (OpenAI text-embedding-3-large, Cohere embed-v3). It provides 32x memory reduction and extremely fast Hamming distance computation, but causes significant accuracy loss with incompatible models. Test recall before deploying.

**Product quantization:** Use for very high-dimensional vectors (1536+) when you need more compression than scalar but more accuracy than binary. Product quantization divides the vector into sub-vectors and quantizes each independently, achieving 8-32x compression.

**No quantization:** Keep full float32 vectors when accuracy is paramount and RAM is not a constraint. Also appropriate for small datasets (< 100K vectors) where memory isn't an issue.

### Q: How do I handle multi-tenancy -- many customers sharing one Qdrant instance?

**Payload-based filtering (recommended for most cases):** Add a `tenant_id` field to every point's payload and create a keyword index on it. Include `tenant_id` in every query's filter. Qdrant's filterable HNSW handles this efficiently because the filter-aware graph construction creates sub-graph connections per tenant value.

```python
# Create index for tenant isolation
client.create_payload_index("shared", "tenant_id", "keyword")

# Every search includes the tenant filter
client.query_points("shared", query=vec, query_filter={
    "must": [{"key": "tenant_id", "match": {"value": "customer_42"}}]
}, limit=10)
```

**Shard-per-tenant (for large tenants):** Since v1.16, Qdrant supports tiered multitenancy with user-defined sharding. Large tenants get dedicated shards, while small tenants share a common fallback shard. This provides physical isolation for large tenants (better performance, independent scaling) while keeping infrastructure costs low for small tenants.

**Collection-per-tenant (simplest isolation):** Create a separate collection per tenant. This provides the strongest isolation but scales poorly beyond a few hundred tenants due to per-collection overhead (HNSW graphs, optimizer processes, memory).

### Q: How do I optimize search latency for production workloads?

1. **Enable scalar quantization** with `always_ram=true`. This keeps quantized vectors in RAM for fast initial scoring while allowing original vectors to live on disk for rescoring.

2. **Tune `hnsw_ef`** at query time. Start with the default (128) and measure recall vs. latency. For latency-critical workloads, try lowering to 64-96. For recall-critical workloads, increase to 256-512.

3. **Build payload indexes** on all fields used in filters. Without an index, Qdrant must evaluate filters by scanning payload data, which is orders of magnitude slower than indexed lookup.

4. **Use `indexed_only: true`** in search parameters to skip searching unindexed (appendable) segments. This sacrifices seeing very recently ingested data but provides more consistent latency.

5. **Right-size the HNSW parameters.** Higher `m` (32-64) provides better recall but uses more RAM and slows search (more neighbors to score per hop). The default `m=16` is a good starting point for most workloads.

6. **Monitor the optimizer.** If segment count keeps growing, the optimizer is falling behind ingestion. Increase `indexing_threshold` to reduce optimization frequency, or scale horizontally.

### Q: How does Qdrant compare to just using pgvector in PostgreSQL?

pgvector adds vector similarity search to PostgreSQL, which is compelling if you already run PostgreSQL and want to avoid a new service. However, there are significant differences:

**Performance:** Qdrant is typically 5-20x faster than pgvector for similarity search, especially with filtering. Qdrant's HNSW implementation is purpose-built with SIMD-optimized distance functions, while pgvector's is a general-purpose PostgreSQL extension. Qdrant's filterable HNSW integrates filtering into graph traversal; pgvector must pre-filter or post-filter, losing performance on selective queries.

**Scalability:** Qdrant supports horizontal scaling via sharding and replication across multiple nodes. pgvector is limited to PostgreSQL's scalability options (read replicas, partitioning), which don't distribute the vector index.

**Features:** Qdrant offers sparse vectors, named multi-vectors, multiple quantization methods, hybrid search with RRF, and recommendation APIs. pgvector offers basic dense vector search with HNSW or IVFFlat indexes.

**When pgvector wins:** If your dataset is small (< 1M vectors), your filtering is simple, you want a single database for both relational and vector data, and operational simplicity matters more than peak performance. pgvector eliminates the need to manage a separate vector database.

**When Qdrant wins:** If you need high-performance filtered search, scale beyond a single node, require advanced features (quantization, sparse vectors, hybrid search), or are building a dedicated AI/ML application where vector search is the primary workload.

### Q: What's the maximum dataset size Qdrant can handle on a single node?

With appropriate configuration, a single Qdrant node can handle 100M+ vectors:

- **100M vectors at 768 dimensions with scalar quantization:** ~76 GB for quantized vectors + ~12 GB for HNSW graph + payload overhead. Fits on a machine with 128 GB RAM with room for OS and page cache.
- **100M vectors at 1536 dimensions with scalar quantization and mmap:** Quantized vectors in RAM (~150 GB), original vectors on disk. Requires 256 GB+ RAM for optimal performance.

The practical limit is determined by RAM for the HNSW graph (which must fit in memory for reasonable query latency) and disk I/O for mmap'd data. Beyond ~200M vectors on a single node, distributed deployment with multiple shards is recommended.

Qdrant's benchmarks show 3ms p99 latency for 1M OpenAI embeddings and sub-10ms latency for 10M vectors with appropriate quantization and hardware.

### Q: How does Qdrant handle updates and deletes -- does HNSW support them?

Qdrant handles updates through its segment-based architecture rather than modifying the HNSW graph directly:

**Upserts:** New or updated points go to the appendable segment. The existing point (if updating) is soft-deleted in its current segment via the ID tracker (marked as deleted but not removed from the graph). The new version exists in the appendable segment. During search, the ID tracker ensures only the latest version is returned.

**Deletes:** Points are soft-deleted via the ID tracker. They remain in the HNSW graph but are excluded from search results. The VacuumOptimizer periodically reclaims space by rebuilding segments without deleted points.

**Why not modify HNSW in-place?** Removing a node from an HNSW graph requires rewiring its neighbors, which is complex, slow, and risks degrading graph quality. Qdrant's approach of soft-deleting and periodic rebuilding is simpler, faster for individual operations, and produces better graph quality because rebuilds create optimal connections from scratch.

The trade-off is that heavily deleted segments waste space until vacuum runs. Monitor the `deleted_points` metric and ensure the VacuumOptimizer is keeping up.
