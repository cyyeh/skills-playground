## Trade-offs & Limitations
<!-- level: intermediate -->
<!-- references:
- [Vector Database Comparison (LiquidMetal AI)](https://liquidmetal.ai/casesAndBlogs/vector-comparison/) | blog
- [Best Vector Databases 2026 (Firecrawl)](https://www.firecrawl.dev/blog/best-vector-databases) | blog
- [Qdrant Documentation](https://qdrant.tech/documentation/) | official-docs
- [Vector Database Comparison (TensorBlue)](https://tensorblue.com/blog/vector-database-comparison-pinecone-weaviate-qdrant-milvus-2025) | blog
-->

### Strengths

**Rust Performance:** Qdrant's Rust implementation delivers excellent performance with predictable resource usage. There is no garbage collector causing latency spikes, no JVM warm-up time, and memory usage stays tightly controlled. This translates to consistent sub-millisecond internal processing times and reliable tail latencies under load.

**Rich Payload Filtering:** Qdrant's filtering capabilities are among the most sophisticated in the vector database space. Filters are integrated into the HNSW traversal (not post-processing), supporting keyword, numeric range, geo, datetime, full-text, and nested field conditions with boolean logic. This makes Qdrant especially strong for applications that need "find me similar items WHERE..." queries.

**Flexible Quantization:** Three quantization methods (scalar, binary, product) with configurable variants (1.5-bit, 2-bit) give fine-grained control over the memory-accuracy-speed trade-off. The rescoring pipeline with configurable oversampling maintains high recall even with aggressive compression.

**Simple Deployment:** A single binary or Docker container gets you running. No external dependencies (no ZooKeeper, no etcd, no separate metadata store). Distributed mode uses built-in Raft consensus. The Python client's local mode lets you develop without even running a server.

**Named Vectors and Multi-Vector Support:** Storing multiple vector types per point enables multi-modal search, hybrid dense+sparse retrieval, and late-interaction models like ColBERT — capabilities that many competitors lack or implement as afterthoughts.

### Limitations

**No Built-in Embedding Generation:** Unlike Weaviate (which can call embedding models during ingestion), Qdrant requires you to generate embeddings externally and pass them to the API. This adds a step to the pipeline, though the FastEmbed library mitigates this for Python users.

**Approximate Search Only:** HNSW is an approximate algorithm. While recall is typically 95-99%+ in practice, it is not guaranteed to return the exact nearest neighbors. Applications requiring 100% exact search must use brute-force mode, which does not scale beyond small collections.

**Memory Requirements for Large Indexes:** The HNSW graph structure itself requires significant memory (proportional to `num_points * m * 2 * 8 bytes`). For very large collections without memmap, memory requirements can be substantial. Quantization helps with vector memory but does not reduce graph overhead.

**Segment Optimization Latency:** Newly upserted points are immediately searchable via brute-force in the appendable segment, but they do not benefit from HNSW indexing until the optimizer builds the index (triggered at the indexing threshold). This means very recent points may have slightly higher search latency.

**Limited Query Language:** Qdrant's filtering uses a JSON-based query language rather than SQL. While powerful, it lacks the expressiveness of SQL for complex joins, aggregations, or subqueries. Qdrant is a search engine, not a general-purpose database.

### Alternatives Comparison

| Feature | Qdrant | Pinecone | Weaviate | Milvus | pgvector | Chroma |
|---------|--------|----------|----------|--------|----------|--------|
| **Language** | Rust | Proprietary | Go | Go/C++ | C (Postgres ext) | Python |
| **License** | Apache-2.0 | Proprietary | BSD-3 | Apache-2.0 | PostgreSQL | Apache-2.0 |
| **Self-hosted** | Yes | No | Yes | Yes | Yes | Yes |
| **Managed cloud** | Yes | Yes (only) | Yes | Yes (Zilliz) | Various | Yes |
| **Filtering** | Excellent | Good | Good | Good | SQL (excellent) | Basic |
| **Quantization** | Scalar/Binary/Product | Automatic | Binary/PQ | IVF/PQ/DiskANN | None (HNSW only) | None |
| **Distributed** | Built-in Raft | Managed | Built-in Raft | Kubernetes-native | Postgres replicas | No |
| **Sparse vectors** | Yes | Yes | No | Yes | No | No |
| **Multi-vector** | Yes (named vectors) | No | No | No | No | No |
| **Scale ceiling** | Billions | Billions | Hundreds of millions | Billions | ~100M practical | Millions |
| **Best for** | Filtered search + production | Zero-ops cloud | Knowledge graphs + semantic | GPU-accelerated scale | SQL-first teams | Prototyping |

### When to Choose Qdrant

- You need rich payload filtering combined with vector search.
- You want an open-source solution you can self-host and customize.
- You care about memory efficiency and want flexible quantization options.
- You need multi-vector support (dense + sparse, multi-modal).
- You want a Rust-based engine with predictable performance characteristics.

### When to Choose Something Else

- **Pinecone** if you want zero-ops managed vector search and do not need self-hosting.
- **Weaviate** if you need built-in embedding generation (vectorizer modules) and a GraphQL interface.
- **Milvus** if you need GPU-accelerated indexing and search at massive scale with Kubernetes-native deployment.
- **pgvector** if your vector search needs are modest and you want to keep everything in PostgreSQL.
- **Chroma** if you need a lightweight, Python-native vector store for prototyping and small-scale applications.

### The Honest Take

Qdrant occupies a strong position in the vector database landscape: it is the go-to choice for teams that need a self-hosted, production-grade vector database with excellent filtering and memory efficiency. Its Rust foundation provides a genuine performance advantage over Go- and Python-based alternatives. The combination of rich filtering, flexible quantization, and multi-vector support makes it particularly well-suited for complex production applications like multi-tenant RAG systems.

The main trade-offs are the lack of built-in embedding generation (you need to bring your own embeddings) and the JSON query language (less familiar than SQL for some teams). For teams that want zero-ops simplicity, Pinecone remains the path of least resistance. For teams invested in the Kubernetes ecosystem at billion-scale, Milvus is worth evaluating. But for the broad middle ground of production vector search applications, Qdrant delivers an excellent balance of performance, flexibility, and operational simplicity.
