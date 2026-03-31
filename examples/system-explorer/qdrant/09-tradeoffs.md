## Trade-offs & Limitations
<!-- level: intermediate -->
<!-- references:
- [Vector Database Comparison 2025](https://tensorblue.com/blog/vector-database-comparison-pinecone-weaviate-qdrant-milvus-2025) | blog
- [Built for Vector Search](https://qdrant.tech/articles/dedicated-vector-search/) | blog
- [Qdrant High-Performance Vector Search Engine](https://qdrant.tech/qdrant-vector-database/) | official-docs
- [Vector Database Comparison: Pinecone vs Weaviate vs Qdrant](https://liquidmetal.ai/casesAndBlogs/vector-comparison/) | blog
-->

### Strengths

**Purpose-built Rust engine with predictable latency.** Qdrant's decision to write everything in Rust with a custom storage engine (Gridstore) pays off in production. No garbage collection pauses, no JVM heap tuning, no Python GIL contention. The result is [sub-20ms p50 query latency](https://qdrant.tech/qdrant-vector-database/) at billion-scale with tight p99 variance. For latency-sensitive applications (real-time recommendations, conversational AI), this predictability matters more than raw throughput numbers.

**Best-in-class filtered vector search.** Qdrant's filterable HNSW implementation -- integrating payload conditions directly into graph traversal with adaptive query planning -- is arguably the strongest differentiator against competitors. Most vector databases either pre-filter (breaking graph connectivity) or post-filter (wasting compute). Qdrant's approach maintains high recall even with restrictive filters, and the query planner automatically switches strategies based on estimated cardinality. For real-world workloads where nearly every search includes metadata filters, this translates to consistently better recall and latency.

**Full spectrum of quantization options.** Supporting scalar, product, and binary quantization -- plus asymmetric combinations (binary stored / scalar query) and configurable oversampling -- gives operators fine-grained control over the memory/accuracy/speed trade-off. The ability to keep quantized vectors in RAM while offloading originals to disk is a practical production pattern that competitors like Weaviate and Pinecone do not expose with the same granularity.

**Flexible deployment model.** From a single Docker container on a laptop, to a multi-node cluster on Kubernetes, to Qdrant Edge on devices, to a fully managed cloud service -- the same codebase runs everywhere. This is valuable for organizations that start prototyping locally and need to move to production without re-architecting. The Apache 2.0 license and self-hosted option mean no vendor lock-in.

**Rich payload model with native filtering.** Payloads support nested JSON objects, arrays, geo-points, datetime values, and full-text tokenization -- with indexed filtering on all types. This is closer to a document database's metadata capabilities than what most vector databases offer, reducing the need for a separate metadata store alongside the vector index.

### Limitations

**Eventual consistency for point operations.** Because point-level writes bypass Raft consensus and propagate directly to replicas, there is a window where different replicas have different data. Applications that write and immediately read (e.g., "store this vector and immediately search for it") may not find the just-written point unless they use `read_consistency: "all"`, which adds latency. This is a deliberate trade-off for write throughput, but it surprises teams accustomed to strongly-consistent databases.

**HNSW index rebuild cost on bulk updates.** Large bulk updates (replacing >10% of vectors in a collection) trigger expensive segment optimization cycles -- the optimizer must rebuild HNSW indexes on newly compacted segments. During this window, freshly inserted points reside in mutable segments with scan-based search, which is slower than HNSW for large segments. Workloads with frequent full re-indexing (e.g., nightly embedding model retraining with complete vector replacement) may experience sustained periods of suboptimal search performance. Incremental HNSW indexing (added in 2025) mitigates this for partial updates but does not eliminate it for full rebuilds.

**No cross-collection operations.** Qdrant operates strictly within single collections -- there are no joins, cross-collection queries, or transactions spanning multiple collections. If your application needs to correlate results across different vector spaces (e.g., "find similar images AND similar text descriptions"), you must perform separate queries and merge results in application code. This is a fundamental limitation of the single-collection architecture.

**Memory pressure at extreme scale without quantization.** Without quantization, Qdrant's memory requirements scale linearly with vector count and dimensionality. A billion 768-dimensional float32 vectors require ~2.9 TB of RAM for vectors alone, plus HNSW graph overhead. Quantization reduces this dramatically (to ~72 GB with scalar, ~9 GB with binary), but organizations that cannot accept any accuracy loss from quantization face steep hardware costs. Competing solutions like Milvus offer disk-based indexing (DiskANN) as an alternative to RAM-based quantization.

**Operational complexity in distributed mode.** While Qdrant's distributed features are powerful, operating a multi-node cluster requires understanding Raft consensus, shard placement, replica state machines (9 distinct states), transfer methods, and consistency tuning. The learning curve is steeper than fully managed alternatives like Pinecone, where scaling is abstracted away. Debugging shard transfer failures or replica state inconsistencies requires familiarity with the internal state machine.

### Alternatives Comparison

| Feature | Qdrant | Pinecone | Milvus | Weaviate | pgvector |
|---------|--------|----------|--------|----------|----------|
| **Language** | Rust | Proprietary (managed) | Go + C++ | Go | C (PG extension) |
| **Deployment** | Self-hosted / Cloud / Edge | Managed only | Self-hosted / Zilliz Cloud | Self-hosted / Cloud | PostgreSQL extension |
| **License** | Apache 2.0 | Proprietary | Apache 2.0 | BSD-3-Clause | PostgreSQL License |
| **Filtered search** | Filterable HNSW (in-traversal) | Post-filter + metadata index | Attribute filtering | Pre-filter + HNSW | WHERE clause + HNSW |
| **Quantization** | Scalar, Product, Binary | Automatic (not configurable) | Scalar, Product, IVF-SQ8 | Product, Binary | None (HNSW only) |
| **Sparse vectors** | Native support | No native sparse | Native support | BM25 module | No |
| **Horizontal scaling** | Built-in sharding + replication | Automatic | Disaggregated compute/storage | Built-in sharding | No native sharding |
| **GPU acceleration** | Index construction | N/A | Index construction + search | No | No |

**[Pinecone](https://www.pinecone.io/)** -- The easiest on-ramp for teams that want zero operational overhead. Pinecone is fully managed and serverless, abstracting away all infrastructure concerns. It is the better choice when your team lacks DevOps capacity to run databases and can accept the higher per-query cost and vendor lock-in of a proprietary service. Qdrant is better when you need self-hosted deployment, fine-grained quantization control, or the cost profile of open-source software at scale.

**[Milvus](https://milvus.io/) / Zilliz Cloud** -- The strongest competitor for enterprise-scale deployments. Milvus has a more mature disaggregated architecture (separating compute, storage, and coordination), supports DiskANN for disk-based indexing, and has been tested at larger scale (billions of vectors in production at multiple companies). Choose Milvus when you need the most battle-tested distributed architecture and are willing to accept its higher operational complexity (multiple components: etcd, MinIO, Pulsar/Kafka). Choose Qdrant when you prefer a simpler single-binary architecture, need stronger filtered search, or want Rust's performance predictability.

**[Weaviate](https://weaviate.io/)** -- Differentiates with built-in vectorization modules (you send text, Weaviate calls the embedding model) and a GraphQL query interface. Choose Weaviate when you want an all-in-one solution that handles embedding generation alongside storage and search, or when your team prefers GraphQL over REST/gRPC. Choose Qdrant when you want to control the embedding pipeline yourself, need finer-grained quantization, or prioritize raw search performance over convenience features.

**[pgvector](https://github.com/pgvector/pgvector)** -- The pragmatic choice when vector search is a secondary feature in a PostgreSQL-centric application. Zero additional infrastructure, full SQL power, and transactional consistency with your relational data. Choose pgvector for workloads under 10M vectors where you do not need advanced features (quantization, hybrid search, horizontal scaling). Choose Qdrant when vector search is a primary workload with dedicated performance and scaling requirements.

### The Honest Take

Qdrant is the right choice for teams that need a self-hosted, production-grade vector database with strong filtered search, flexible quantization, and Rust's performance guarantees. It hits a sweet spot between Pinecone's "zero ops" simplicity and Milvus's "enterprise-scale" complexity. If you want full control over your vector infrastructure without running a multi-component distributed system, Qdrant is the best option in the open-source space today.

It is not the right choice if you need zero-operational-overhead managed service (choose Pinecone), if you need battle-tested billion-scale distributed deployments with disaggregated storage (choose Milvus), or if vector search is a minor feature alongside a transactional SQL workload (choose pgvector). Qdrant's eventual consistency model and HNSW rebuild costs also make it a poor fit for workloads that demand strong consistency or undergo frequent complete re-indexing.
