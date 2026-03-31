## Common Q&A
<!-- level: all -->
<!-- references:
- [Qdrant Documentation](https://qdrant.tech/documentation/) | official-docs
- [Qdrant GitHub Discussions](https://github.com/orgs/qdrant/discussions) | github
- [Qdrant Quantization Documentation](https://qdrant.tech/documentation/manage-data/quantization/) | official-docs
-->

### Q: How does Qdrant compare to using pgvector with PostgreSQL?

**A:** pgvector adds vector similarity search to an existing PostgreSQL database, which is convenient if you already use Postgres and have modest vector search needs (up to ~10-100M vectors). Qdrant is purpose-built for vector search with a dedicated HNSW implementation, rich payload filtering, multiple quantization options, native distributed mode, and significantly better performance at scale. Choose pgvector when you want to keep everything in one database and your vector workload is secondary. Choose Qdrant when vector search is a core part of your application and you need production-grade performance, scaling, or advanced features like quantization and filtered HNSW search.

### Q: How much memory does Qdrant need for my dataset?

**A:** The memory formula depends on your storage and quantization configuration. For in-memory storage without quantization: `vectors = num_points * dimensions * 4 bytes` (float32) plus the HNSW graph overhead (`~num_points * m * 2 * 8 bytes` for neighbor links). For 1M vectors at 1536 dimensions with m=16: vectors = ~5.7 GB, HNSW = ~256 MB, total ~6 GB. With scalar quantization (4x compression on vectors): ~1.7 GB. With memmap storage, the OS page cache manages what's in RAM — you can serve datasets much larger than available memory with graceful performance degradation.

### Q: What is the maximum number of vectors Qdrant can handle?

**A:** A single Qdrant node can handle tens of millions of vectors depending on dimensionality and memory. With distributed mode, Qdrant scales horizontally to billions of vectors by sharding collections across multiple nodes. The practical limit depends on your hardware, dimensionality, quantization strategy, and latency requirements. Qdrant Cloud has been tested with billion-scale deployments.

### Q: Should I use cosine, dot product, or Euclidean distance?

**A:** Use the metric that matches your embedding model's training objective. Most text embedding models (OpenAI, Cohere, sentence-transformers) work best with cosine similarity. If your vectors are already normalized (unit length), dot product is mathematically equivalent to cosine but slightly faster. Euclidean distance is used when absolute magnitude differences matter (e.g., some image feature vectors). Manhattan distance is rarely used but can be robust to outliers. When in doubt, start with cosine — it works well for the vast majority of embedding models.

### Q: When should I use quantization, and which type?

**A:** Use quantization when memory is a bottleneck or when you need to improve search throughput. **Scalar quantization** (int8) is the safest default — 4x memory reduction with less than 1% accuracy loss. Works with any embedding model. **Binary quantization** (1-bit) offers 32x compression and up to 40x speedup but works best with high-dimensional embeddings (>1024d) from models like OpenAI text-embedding-ada-002. Test it with your specific model before committing. **Product quantization** provides the highest compression (up to 64x) but with significant accuracy loss (~0.7 recall) and no speed improvement — use only when memory is extremely constrained.

### Q: How do I handle multi-tenancy in Qdrant?

**A:** Qdrant supports two approaches. **Payload-based filtering:** Store a `tenant_id` field in each point's payload and include it as a filter in every search query. Simple to implement, works well up to moderate tenant counts. Create a keyword index on the tenant field for efficient filtering. **Custom sharding (v1.7.0+):** Assign each tenant to a specific shard key. This provides physical data isolation and allows Qdrant to search only the relevant shard, improving performance for large tenant counts. Qdrant v1.15+ introduced tiered multitenancy for optimized resource sharing across tenants.

### Q: Can Qdrant handle real-time updates or is it batch-only?

**A:** Qdrant supports real-time upserts, deletes, and payload updates. New points are immediately available for brute-force search in the appendable segment. Once the optimizer builds the HNSW index for a segment (triggered at the indexing threshold), those points become available for fast indexed search. There is a brief delay between upsert and HNSW availability, but the point is never invisible — it is always searchable via the appendable segment's brute-force path.

### Q: How does Qdrant ensure data durability?

**A:** All write operations are first persisted to the Write-Ahead Log (WAL) before being acknowledged to the client. The WAL is a sequential, append-only file that survives process crashes and power failures. On recovery, Qdrant replays WAL entries that were not yet applied to segments. Additionally, the flush worker periodically persists segment state to disk (default: every 5 seconds). In distributed mode, replication across multiple nodes provides additional durability — even if a node is permanently lost, data can be recovered from replicas.

### Q: What embedding model should I use with Qdrant?

**A:** The choice depends on your use case, budget, and latency requirements. For general-purpose English text: OpenAI text-embedding-3-small (1536d, good balance of quality and cost) or sentence-transformers all-MiniLM-L6-v2 (384d, free, runs locally). For multilingual: Cohere embed-multilingual-v3.0. For maximum quality: OpenAI text-embedding-3-large (3072d). For on-device embedding without API calls: use Qdrant's FastEmbed library included in the Python client. The key constraint is that all vectors in a collection must use the same model and dimensionality.

### Q: How do I migrate from another vector database to Qdrant?

**A:** The general approach is: (1) export vectors and metadata from your source database, (2) create a collection in Qdrant with matching vector configuration, (3) batch-upsert the data using the Qdrant client. Most migrations involve writing a script that reads from the source, transforms payloads to Qdrant's JSON format, and writes batches of points. The Python client supports batch upsert efficiently. If migrating from a database with different distance metrics or normalization, ensure vectors are compatible with Qdrant's expected format.

### Q: Does Qdrant support hybrid search (combining dense and sparse vectors)?

**A:** Yes. Qdrant supports named vectors, allowing you to store multiple vector types on a single point — for example, a dense embedding from a neural model and a sparse BM25 vector from traditional text retrieval. You can search using either vector independently or combine results using Qdrant's fusion capabilities. This enables hybrid search that leverages both semantic understanding (dense) and keyword precision (sparse), which often outperforms either approach alone.
