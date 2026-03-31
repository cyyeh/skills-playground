## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
<!-- references:
- [Enterprise Search Solutions](https://qdrant.tech/enterprise-solutions/) | official-docs
- [Nyris & Qdrant: Visual Search Case Study](https://qdrant.tech/blog/case-study-nyris/) | blog
- [Vector Search in Production](https://qdrant.tech/articles/vector-search-production/) | blog
- [Qdrant Raises $50M Series B](https://www.businesswire.com/news/home/20260312313902/en/Qdrant-Raises-50-Million-Series-B-to-Define-Composable-Vector-Search-as-Core-Infrastructure-for-Production-AI) | blog
-->

### When to Use It

**Retrieval-Augmented Generation (RAG) pipelines.** When your LLM needs to ground its responses in your organization's documents, knowledge base, or product catalog, Qdrant serves as the retrieval backbone. You embed your documents into vectors, store them with metadata payloads (source, date, access level), and at query time retrieve the most relevant chunks to feed into the LLM context window. Qdrant's filtered search is particularly valuable here -- you can restrict retrieval to specific document categories, date ranges, or access permissions in a single query.

**Semantic search and discovery.** When keyword search fails because users describe what they want in different words than what exists in your data. E-commerce product search ("comfortable running shoes for flat feet"), customer support ticket matching, code search across large codebases, and any scenario where meaning matters more than exact keyword matches. Qdrant handles 10,000+ queries per second on a single node for typical embedding dimensions (768-1536).

**Recommendation systems.** When you have user and item embeddings (from collaborative filtering, content-based models, or two-tower architectures) and need real-time nearest-neighbor retrieval for "users who liked X also liked Y" or "items similar to what you viewed." Payload filters let you apply business rules (availability, region, category) alongside similarity search.

**Multi-modal search.** When your search spans text, images, audio, or video -- all mapped to a shared embedding space by models like CLIP or ImageBind. Qdrant's support for multiple named vectors per point lets you store text and image embeddings on the same record and search by either modality. Hybrid search (dense + sparse vectors with reciprocal rank fusion) further combines semantic and keyword relevance.

**Anomaly and fraud detection.** When you need to identify data points that are unusually far from their nearest neighbors. By embedding transaction patterns, sensor readings, or network traffic into vectors, you can detect outliers that deviate from normal behavior. Qdrant's fast nearest-neighbor search and payload filtering enable real-time anomaly scoring against historical baselines.

### When NOT to Use It

**Simple key-value lookups.** If your primary access pattern is "get the record with ID X" or "get all records where status = active," you do not need a vector database. Redis, PostgreSQL, or DynamoDB will serve point lookups with lower operational complexity and latency. Qdrant adds value only when similarity search is a core requirement.

**Full-text search with complex linguistic features.** If you need stemming, synonym expansion, faceted search, autocomplete, and relevance tuning based on TF-IDF or BM25, Elasticsearch or Apache Solr remain better choices. Qdrant's sparse vectors and full-text filtering handle basic keyword matching, but they do not replace a mature full-text search engine for complex information retrieval workloads.

**Relational data with complex joins.** If your queries involve multi-table joins, aggregations, GROUP BY, or transactions across multiple records, use a relational database. Qdrant's payload filtering is powerful but operates on a single collection -- there is no join capability, foreign keys, or transactional semantics across collections.

**Workloads smaller than ~10,000 vectors.** At very small scale, brute-force search (which Qdrant supports internally via plain segments) is fast enough, and the overhead of maintaining HNSW indexes is unnecessary. Libraries like FAISS or even NumPy's cdist can handle in-memory similarity search for small datasets without the operational cost of running a database server.

**Extremely low-latency requirements (<1ms p99) on individual queries.** While Qdrant is fast (sub-20ms p50 at scale), it is a network service with serialization overhead. If you need sub-millisecond latency for individual vector comparisons and can fit your data in process memory, an in-process library like FAISS, Annoy, or ScaNN avoids the network round-trip entirely.

### Real-World Examples

**Tripadvisor -- Semantic Travel Search.** [Tripadvisor](https://www.businesswire.com/news/home/20260312313902/en/Qdrant-Raises-50-Million-Series-B-to-Define-Composable-Vector-Search-as-Core-Infrastructure-for-Production-AI) uses Qdrant to power semantic search across millions of hotels, restaurants, and attractions. Instead of matching on exact keywords ("pet-friendly hotel with pool in Miami"), the system understands the intent behind natural language queries and retrieves relevant listings even when the wording differs from the listing description. Payload filtering ensures results respect business constraints like availability, price range, and geographic region.

**Nyris -- Visual Search for Retail and Manufacturing.** [Nyris](https://qdrant.tech/blog/case-study-nyris/) powers visual search on large retail websites and industrial manufacturing platforms where users need to identify spare parts by photograph. Users snap a photo of a component, Nyris generates an image embedding, and Qdrant retrieves the most visually similar products from a catalog of millions of items. The system handles real-time queries with sub-second latency, enabling "point your camera and find it" workflows that replace manual catalog browsing.

**Bosch -- Predictive Maintenance in Manufacturing.** [Bosch](https://qdrant.tech/enterprise-solutions/) uses Qdrant for predictive maintenance systems that convert equipment sensor data (vibration, temperature, pressure) into vector representations. By comparing current sensor embeddings against historical patterns of known failure modes, the system detects anomalies before they cause equipment failures. The payload filtering capability allows searching within specific equipment types, time windows, and facility locations, while Qdrant's distributed deployment handles the scale of sensor data across global manufacturing sites.

**HubSpot -- AI-Powered CRM Features.** [HubSpot](https://www.businesswire.com/news/home/20260312313902/en/Qdrant-Raises-50-Million-Series-B-to-Define-Composable-Vector-Search-as-Core-Infrastructure-for-Production-AI) integrates Qdrant to power AI features in their CRM platform, including semantic search across customer interactions, automated email categorization, and intelligent lead scoring. Customer communication embeddings are stored with rich metadata payloads (account tier, industry, lifecycle stage), enabling similarity-based features that combine semantic understanding with structured business data.
