## Trade-offs & Limitations
<!-- level: intermediate -->
<!-- references:
- [Vector Database Comparison 2025](https://tensorblue.com/blog/vector-database-comparison-pinecone-weaviate-qdrant-milvus-2025) | blog
- [Top Vector Database for RAG: Qdrant vs Weaviate vs Pinecone](https://research.aimultiple.com/vector-database-for-rag/) | blog
- [Choosing the Right Vector Database](https://medium.com/@elisheba.t.anderson/choosing-the-right-vector-database-opensearch-vs-pinecone-vs-qdrant-vs-weaviate-vs-milvus-vs-037343926d7e) | blog
-->

### Strengths

**Filtered search performance.** Qdrant's filterable HNSW is its standout feature. Unlike competitors that pre-filter or post-filter (both of which degrade either performance or recall), Qdrant integrates filtering directly into the graph traversal with an adaptive query planner. The result: consistently low latency even with highly selective filters that match only 1% of data. For applications that combine semantic search with metadata constraints (e.g., "similar products in the electronics category under $100"), Qdrant leads the field.

**Rust performance and safety.** Built entirely in Rust with zero garbage collection pauses, SIMD-optimized distance functions, and io_uring for maximum disk throughput. The memory safety guarantees mean no segfaults, buffer overflows, or data corruption from memory bugs -- a significant advantage for production vector databases holding billions of vectors. Benchmarks consistently show Qdrant among the top performers in latency and throughput.

**Quantization flexibility.** Three quantization methods (scalar, product, binary) with asymmetric query support and configurable rescoring give engineers fine-grained control over the memory/accuracy trade-off. The `always_ram` option keeps quantized vectors in RAM while original vectors live on disk, providing a practical middle ground. The inline storage format (CompressedWithVectors) further reduces latency by co-locating quantized vectors with HNSW links.

**Multi-vector and hybrid search.** Named vectors (multiple embeddings per point), sparse vectors (for keyword/BM25 matching), and multi-vectors (ColBERT-style late interaction) in a single system. Hybrid search with Reciprocal Rank Fusion combines dense and sparse results without external fusion logic. This eliminates the need to run separate systems for semantic and keyword search.

**Developer experience.** Clean REST and gRPC APIs, official clients in six languages, local mode in the Python client (no server needed for development), and a generous free tier on Qdrant Cloud. The documentation is comprehensive, and the Discord community is active and helpful.

**Distributed scaling.** Horizontal scaling via sharding and replication with Raft-based consensus for cluster coordination. Tiered multitenancy (v1.16+) supports both payload-based and shard-based tenant isolation. Qdrant Cloud provides managed scaling with automatic shard rebalancing.

### Limitations

**No SQL or relational queries.** Qdrant is a vector database, not a general-purpose database. You can't JOIN collections, run GROUP BY aggregations, or perform complex relational queries. Payload filtering supports AND/OR/NOT conditions on individual fields, but the query language is limited compared to SQL. For applications that need both vector search and relational queries, you'll run Qdrant alongside PostgreSQL.

**Write latency visibility.** New points are written to an appendable segment with a plain vector index. Until the optimizer builds an HNSW index on that segment (which happens asynchronously), newly ingested points are searched via linear scan, which is slower and may provide different recall characteristics than HNSW search. The `indexed_only` search parameter can exclude unindexed segments, but this means very recent data is invisible to searches until optimization completes.

**Operational complexity at scale.** Running a distributed Qdrant cluster requires managing Raft consensus, shard placement, replica states, and capacity planning. While simpler than operating a Kubernetes-based Milvus deployment, it's significantly more operational overhead than using a managed service like Pinecone. Qdrant Cloud eliminates this for teams willing to use a managed offering.

**Memory requirements for HNSW.** The HNSW graph must fit in memory (or at least its frequently-accessed layers) for reasonable query latency. With `m=16`, the graph uses ~256 MB per million points. For very large collections (100M+ points), this means the graph alone requires 25+ GB of RAM even with vectors stored on disk. There's no index-free mode for truly memory-constrained environments (though you can fall back to plain linear scan).

**Limited full-text search.** Qdrant's full-text index supports basic tokenized text search, but it's not comparable to dedicated search engines like Elasticsearch for complex text queries (phrase matching, fuzzy matching, boosting, highlighting). If you need sophisticated full-text search, use Qdrant for vector search and Elasticsearch for text search, or rely on sparse vectors for keyword matching.

**Cold-start latency with mmap.** When using memory-mapped storage, the first queries after restart can be slow as the OS page cache warms up. This is a fundamental limitation of mmap-based storage, not specific to Qdrant, but it affects workloads with strict cold-start SLAs.

### Alternatives Comparison

**Pinecone** -- The managed-first vector database. Pinecone is fully managed with no self-hosting option (other than Pinecone Local for development), which means zero operational overhead but also zero control over infrastructure. Choose Pinecone when: your team doesn't want to manage infrastructure, your scale is moderate (< 50M vectors), and you're on a major cloud provider. Choose Qdrant when: you need self-hosting for data sovereignty, require advanced filtering, need hybrid search, or want to avoid vendor lock-in. Qdrant offers a managed cloud option that provides a middle ground.

**Weaviate** -- A vector database with a knowledge-graph orientation and GraphQL API. Weaviate emphasizes built-in vectorization (integrated embedding models) and schema-first design. Choose Weaviate when: you want the database to handle embedding generation, prefer GraphQL, or need knowledge-graph-style relationships between objects. Choose Qdrant when: you manage your own embeddings, need better filtering performance, want a simpler REST API, or need sparse vector support. Weaviate can struggle with memory at very large scale (> 50M vectors); Qdrant's quantization options provide better memory efficiency.

**Milvus** -- A distributed vector database from Zilliz, built on a microservice architecture with separate query, data, and index nodes. Milvus supports multiple index types (HNSW, IVF, DiskANN, GPU-accelerated) and is designed for massive scale. Choose Milvus when: you need GPU-accelerated indexing, require multiple index algorithm options, or are building at enterprise scale (billions of vectors). Choose Qdrant when: you want simpler deployment (single binary vs. Milvus's multi-service architecture requiring etcd, MinIO, and Pulsar), need better filtered search, or prefer Rust's performance characteristics. Milvus has a steeper learning curve and higher operational overhead.

**pgvector** -- PostgreSQL extension for vector similarity search. Choose pgvector when: you already run PostgreSQL, your dataset is small (< 1M vectors), you want a single database for relational + vector queries, and operational simplicity matters more than peak performance. Choose Qdrant when: you need production-grade vector search performance (5-20x faster), horizontal scaling, advanced features (quantization, sparse vectors, hybrid search), or are building a dedicated AI application. pgvector is "good enough" for prototyping; Qdrant is "purpose-built" for production.

**FAISS** -- Facebook's library for efficient similarity search (not a database). FAISS provides the algorithmic building blocks (HNSW, IVF, PQ) but no server, no persistence, no filtering, no API. Choose FAISS when: you need a low-level library embedded in a Python/C++ application, want maximum control over index configuration, or are doing research. Choose Qdrant when: you need a database with persistence, filtering, API access, distributed scaling, and operational features.

**Chroma** -- A lightweight, developer-friendly vector database focused on AI application prototyping. Choose Chroma when: you're building a quick prototype and want the simplest possible setup. Choose Qdrant when: you need production performance, advanced filtering, quantization, distributed deployment, or your dataset exceeds what fits comfortably in memory on a single machine.

### The Honest Take

Qdrant excels as a production vector database for AI applications that need fast filtered search, flexible quantization, and horizontal scaling. Its Rust foundation provides genuine performance and safety advantages. The filtered HNSW implementation is best-in-class, and the multi-vector/hybrid search capabilities cover the full spectrum of modern retrieval needs.

The honest weakness is that Qdrant is a specialized tool: it does vector search extremely well but nothing else. If you need relational queries, complex analytics, or sophisticated full-text search alongside vector search, you'll run multiple systems. The operational complexity of distributed Qdrant (while less than Milvus) is still non-trivial for small teams, which is why Qdrant Cloud exists.

For most teams building AI applications in 2026, Qdrant is the right default choice for the vector search layer -- it has the performance, features, and ecosystem support to handle production workloads, with enough flexibility to grow from prototype to scale.
