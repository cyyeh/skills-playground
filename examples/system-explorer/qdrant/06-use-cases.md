## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
<!-- references:
- [Qdrant Use Cases](https://qdrant.tech/use-cases/) | official
- [RAG Use Case](https://qdrant.tech/rag/) | official
- [Recommendation Engines](https://qdrant.tech/recommendations/) | official
- [Anomaly Detection](https://qdrant.tech/data-analysis-anomaly-detection/) | official
- [5-Minute RAG with DeepSeek](https://qdrant.tech/documentation/tutorials-build-essentials/rag-deepseek/) | tutorial
-->

### Retrieval-Augmented Generation (RAG)

**The problem:** Large language models have knowledge cutoffs, hallucinate facts, and cannot access private data. RAG solves this by retrieving relevant context from a vector database before generating a response.

**How Qdrant fits:**
1. Documents are split into chunks and embedded using a model (OpenAI, Cohere, sentence-transformers)
2. Embeddings are stored in Qdrant with metadata payloads (source, date, author, etc.)
3. At query time, the user's question is embedded and searched against Qdrant
4. Top-k results are passed as context to the LLM for answer generation

**Why Qdrant excels at RAG:**
- Payload filtering enables scoping retrieval to specific document sets, date ranges, or access levels
- Hybrid search (dense + sparse) captures both semantic meaning and exact keyword matches
- Named vectors allow storing embeddings from multiple models (e.g., a fast small model for initial retrieval, a large model for re-ranking)
- Low-latency gRPC interface keeps RAG response times snappy

**Real-world example:** Dust, a platform enabling companies to deploy LLM-powered AI assistants across organizations, chose Qdrant for its RAG pipeline due to ease of deployment and high performance at scale.

### Semantic Search

**The problem:** Traditional keyword search misses synonyms, paraphrases, and conceptual connections. Searching for "how to fix a broken pipe" should find plumbing articles, not just documents containing those exact words.

**How Qdrant fits:**
- Text is converted to dense embeddings that capture meaning
- Search queries find semantically similar content regardless of exact wording
- Payload filters add business logic (date ranges, categories, access control)
- Full-text payload indexes enable hybrid keyword + semantic search

**Use cases:**
- Enterprise knowledge base search
- Customer support ticket matching
- Legal document discovery
- Academic paper similarity

### Recommendation Systems

**The problem:** Recommending similar or complementary items based on user behavior, item features, or collaborative signals.

**How Qdrant fits:**
- Items are represented as vectors (from content features, collaborative filtering, or hybrid models)
- Qdrant's Recommendation API accepts positive and negative example points
- The "best score" strategy evaluates candidates against multiple vectors to improve relevance
- Payload filtering limits recommendations to relevant categories, availability, or pricing

**Use cases:**
- E-commerce product recommendations
- Content recommendation (articles, videos, music)
- Job-candidate matching
- Dating/social matching platforms

### Anomaly Detection

**The problem:** Identifying unusual patterns, outliers, or novel events in data streams.

**How Qdrant fits:**
- Normal behavior patterns are stored as vectors
- Incoming data points are compared against the known distribution
- Points with high distance from their nearest neighbors are flagged as anomalies
- Qdrant supports "dissimilarity search" — finding points farthest from a query

**Use cases:**
- Cybersecurity threat detection
- Financial fraud detection
- Manufacturing quality control
- Network intrusion detection

### Image and Multimodal Search

**The problem:** Finding visually or semantically similar images, or searching across modalities (text-to-image, image-to-text).

**How Qdrant fits:**
- Images are embedded using vision models (CLIP, SigLIP, DINOv2)
- Named vectors allow storing both text and image embeddings per item
- Cross-modal search finds images from text queries or similar images from image queries

**Use cases:**
- E-commerce visual search ("find products that look like this")
- Content moderation (finding similar flagged content)
- Digital asset management
- Medical image retrieval

### When NOT to Use Qdrant

Qdrant is not the right tool for every problem:

- **Exact keyword search only** — If you only need traditional full-text search without semantic understanding, Elasticsearch or Solr are more mature
- **Relational queries** — Qdrant is not a general-purpose database. Complex joins, transactions, and SQL queries belong in PostgreSQL or similar
- **Fewer than 10,000 vectors** — At small scale, brute-force search in application memory may be simpler and fast enough
- **Strict ACID transactions** — Qdrant offers eventual consistency by default in distributed mode; it is not designed for banking-style transactional guarantees
- **Batch-only analytics** — If you only run periodic batch similarity computations without serving real-time queries, libraries like FAISS or Annoy may suffice
