## Trade-offs & Limitations
<!-- level: intermediate -->
<!-- references:
- [Vector Database Comparison 2025-2026](https://www.firecrawl.dev/blog/best-vector-databases) | comparison
- [Vector DB Comparison: Pinecone vs Weaviate vs Qdrant vs FAISS vs Milvus vs Chroma](https://liquidmetal.ai/casesAndBlogs/vector-comparison/) | comparison
- [Choosing the Right Vector Database](https://medium.com/@elisheba.t.anderson/choosing-the-right-vector-database-opensearch-vs-pinecone-vs-qdrant-vs-weaviate-vs-milvus-vs-037343926d7e) | comparison
- [Qdrant Review: A Highly Flexible Option for Vector Search](https://www.infoworld.com/article/3477585/qdrant-review-a-highly-flexible-option-for-vector-search.html) | review
-->

### Strengths

1. **Best-in-class filtered search** — Qdrant's filterable HNSW is its crown jewel. While other databases apply filters after vector search (losing accuracy) or before (losing performance), Qdrant integrates filtering into the graph traversal itself. This produces both fast and accurate results for filtered queries.

2. **Rust performance with no GC pauses** — As the only major vector DB written entirely in Rust, Qdrant delivers predictable, low-latency performance without garbage collection stops. This matters for p99 latency-sensitive production workloads.

3. **Rich vector type support** — Dense, sparse, and multi-dense vectors in a single collection. Named vectors allow multiple embedding spaces per point. This natively supports hybrid search and late-interaction re-ranking without external orchestration.

4. **Flexible quantization** — Three quantization methods (scalar, product, binary) with configurable parameters. Asymmetric quantization (different precision for stored vectors vs. query vectors) further optimizes the speed-accuracy tradeoff.

5. **Production-ready distributed mode** — Horizontal sharding, configurable replication, Raft consensus for metadata, and per-operation consistency levels. Custom sharding enables efficient multi-tenancy.

6. **Strong API design** — Clean REST and gRPC APIs with official SDKs in six languages. The Query API unifies search, recommendation, and hybrid search into a single composable interface.

7. **Active development** — Regular releases (1.15, 1.16, 1.17 in rapid succession) with significant features: Gridstore replacing RocksDB, Qdrant Edge for in-process use, tiered multitenancy, ACORN algorithm.

### Limitations

1. **Smaller community than Milvus** — Milvus has ~25K GitHub stars vs. Qdrant's ~9K (as of early 2025). This means fewer community-contributed integrations, tutorials, and Stack Overflow answers.

2. **No built-in embedding generation** — Unlike Weaviate (which has vectorizer modules), Qdrant does not generate embeddings. You must handle embedding creation separately. This is by design (separation of concerns) but adds integration complexity.

3. **Immutable shard count** — Once a collection is created, you cannot change its shard_number. If you underestimate growth, you must create a new collection and re-ingest data. This is a common operational pain point.

4. **Memory-intensive for full-precision search** — Without quantization or mmap, RAM requirements scale linearly with vector count. 100M vectors at 768 dimensions requires ~460 GB RAM at full precision.

5. **No multi-document transactions** — Each point operation is atomic, but there is no way to atomically update multiple points or perform cross-collection operations. This limits some advanced consistency patterns.

6. **Limited analytics capabilities** — Qdrant is focused on similarity search, not analytics. You cannot run aggregations, GROUP BY, or SQL-style queries over payloads. For that, you need to combine Qdrant with an analytical database.

7. **Sparse vector ecosystem is younger** — While dense vector support is mature, sparse vector support (introduced in v1.7) and hybrid search patterns are newer and have fewer production battle scars compared to established full-text search engines.

### Comparison with Alternatives

#### Qdrant vs. Pinecone

| Aspect | Qdrant | Pinecone |
|--------|--------|----------|
| **Deployment** | Self-hosted or managed cloud | Fully managed only |
| **Source code** | Open-source (Apache 2.0) | Proprietary |
| **Filtering** | Filterable HNSW (during search) | Post-search filtering |
| **Vector types** | Dense, sparse, multivector | Dense, sparse |
| **Cost at scale** | Lower (self-hosted option) | Higher (managed pricing) |
| **Ease of setup** | Moderate (Docker/K8s) | Very easy (SaaS) |
| **Best for** | Teams needing control + filters | Teams wanting zero-ops |

#### Qdrant vs. Weaviate

| Aspect | Qdrant | Weaviate |
|--------|--------|----------|
| **Language** | Rust | Go |
| **Vectorizer modules** | No (bring your own) | Yes (built-in) |
| **Filtering** | Filterable HNSW | Pre-filter + HNSW |
| **Hybrid search** | Dense + sparse fusion | BM25 + vector fusion |
| **GraphQL API** | No | Yes |
| **Best for** | Performance + filtered search | Hybrid search + built-in ML |

#### Qdrant vs. Milvus

| Aspect | Qdrant | Milvus |
|--------|--------|--------|
| **Language** | Rust | Go + C++ |
| **Scale** | Millions to low billions | Billions (proven at massive scale) |
| **Index types** | HNSW (primary) | IVF, HNSW, DiskANN, GPU indexes |
| **Community** | ~9K stars | ~25K stars |
| **Operational complexity** | Lower (single binary) | Higher (etcd, MinIO, Pulsar deps) |
| **Best for** | Mid-scale with rich filtering | Massive scale with varied index needs |

#### Qdrant vs. pgvector

| Aspect | Qdrant | pgvector |
|--------|--------|----------|
| **Architecture** | Purpose-built vector DB | PostgreSQL extension |
| **Performance at scale** | ~40 QPS at 50M vectors (99% recall) | ~470 QPS at 50M vectors (with pgvectorscale) |
| **Filtering** | Filterable HNSW | SQL WHERE clauses |
| **Operational overhead** | Separate service | Same PostgreSQL instance |
| **Max practical scale** | Billions (distributed) | 10-100M (single instance) |
| **Best for** | Dedicated vector workloads | PostgreSQL-centric stacks <100M vectors |

#### Qdrant vs. Chroma

| Aspect | Qdrant | Chroma |
|--------|--------|--------|
| **Target** | Production workloads | Prototyping and small-scale |
| **Distributed mode** | Yes (sharding + replication) | Limited |
| **Quantization** | Scalar, product, binary | None |
| **Maturity** | Production-proven | Rapid development stage |
| **Best for** | Production at any scale | Quick prototypes and local dev |

### Decision Framework

**Choose Qdrant when:**
- You need fast filtered vector search in production
- You want open-source with self-hosting flexibility
- You need hybrid search (dense + sparse) natively
- You value predictable latency (Rust, no GC)
- You need multi-tenancy with custom sharding

**Consider alternatives when:**
- You want fully managed with zero ops (Pinecone)
- You need built-in vectorizer modules (Weaviate)
- You're operating at true billion-scale with diverse indexes (Milvus)
- You have a PostgreSQL-centric stack with <100M vectors (pgvector)
- You're just prototyping (Chroma)
