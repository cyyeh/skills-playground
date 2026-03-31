## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
<!-- references:
- [Qdrant RAG Use Case](https://qdrant.tech/rag/) | official-docs
- [Qdrant AI Agents](https://qdrant.tech/ai-agents/) | official-docs
- [Qdrant Raises $50M Series B](https://www.businesswire.com/news/home/20260312313902/en/) | news
- [Qdrant Vector Database in GenAI Projects](https://www.karimarttila.fi/genai/2026/03/04/qdrant-vector-database-in-genai-projects.html) | blog
-->

### When to Use It

**Retrieval-Augmented Generation (RAG).** You have a corpus of documents (knowledge base, documentation, internal wikis) and want an LLM to answer questions grounded in that corpus. Qdrant stores document chunk embeddings, and when a user asks a question, the query is embedded, the most relevant chunks are retrieved via similarity search, and those chunks are passed to the LLM as context. Qdrant's payload filtering enables scoping retrieval to specific document categories, date ranges, or access levels -- critical for production RAG systems with multi-tenancy.

**Semantic Search.** You need search that understands meaning rather than just keywords. Traditional search engines match exact terms; Qdrant matches concepts. A search for "affordable family vacation" returns results about "budget-friendly trips with kids" even though no words overlap. Qdrant's hybrid search (combining dense semantic vectors with sparse keyword vectors via Reciprocal Rank Fusion) delivers the best of both worlds.

**Recommendation Systems.** You have user behavior data (views, purchases, likes) and want to recommend similar items. Embed items and users into the same vector space, then use Qdrant to find items most similar to a user's preference vector or to items they've already interacted with. Qdrant's recommendation API supports positive and negative examples, allowing nuanced "more like this, less like that" recommendations.

**AI Agent Memory.** AI agents need long-term memory that persists across conversations. Qdrant stores embeddings of past interactions, tool outputs, and learned facts. When the agent needs to recall relevant context, it queries Qdrant with the current conversation embedding. Qdrant's payload filtering enables time-based retrieval ("what did the user say last week?") and topic-based retrieval ("what do we know about their project preferences?").

**Image and Multimodal Search.** With CLIP or similar multimodal embedding models, you can embed both images and text into the same vector space. Qdrant then enables cross-modal search: find images matching a text description, or find text descriptions matching an image. Named vectors allow storing both modalities in a single point, searched independently.

**Anomaly Detection.** Embed normal behavior patterns as vectors. New observations that are far from all stored vectors (low maximum similarity score) are anomalies. Qdrant's fast nearest-neighbor search makes this real-time: check each new event against the database of normal patterns and flag outliers instantly.

### When NOT to Use It

**Traditional relational queries.** If your primary need is SQL joins, aggregations, transactions, and ACID compliance on structured data, use PostgreSQL. Qdrant is not a general-purpose database -- it's optimized for similarity search, not complex relational queries. You can filter by payload fields, but you can't JOIN collections or run GROUP BY aggregations.

**Small datasets (< 10K vectors).** For very small collections, the overhead of running a Qdrant server isn't justified. Use a simple brute-force search in NumPy/FAISS, or use the `qdrant-client` in local mode (in-memory, no server). The HNSW index overhead only pays off when exact search becomes too slow.

**Exact keyword matching only.** If your search needs are purely lexical (exact string matching, regex, traditional full-text search), use Elasticsearch or PostgreSQL full-text search. Qdrant's full-text index is basic compared to dedicated search engines. However, if you need both semantic and keyword search, Qdrant's hybrid search (dense + sparse vectors) is a strong option.

**Write-heavy transactional workloads.** Qdrant's segment-based architecture is optimized for read-heavy workloads with background optimization of writes. If your application requires high-frequency, low-latency writes with immediate consistency (e.g., financial transactions), use a traditional database. Qdrant's writes go through WAL and background optimization, introducing a delay before new points are fully indexed.

**Structured analytics.** If you need to compute analytics over your data (average prices, count by category, time-series aggregations), Qdrant is the wrong tool. It returns individual points ranked by similarity, not aggregated statistics. Pair it with an analytical database for those needs.

### Real-World Examples

**Tripadvisor -- Travel Recommendation at Scale**
Tripadvisor uses Qdrant to power semantic search and recommendation across millions of hotels, restaurants, and attractions. User queries and listing descriptions are embedded into a shared vector space, enabling searches that understand travel intent ("cozy beachfront hotel with snorkeling") rather than just keyword matching. Qdrant's payload filtering handles the complex structured constraints (location, price range, rating, amenities) that travel search demands.

**HubSpot -- CRM Intelligence**
HubSpot integrates Qdrant into their CRM platform to provide AI-powered features: finding similar companies, matching contacts to ideal customer profiles, and surfacing relevant content recommendations. Qdrant's multi-tenancy capabilities (payload-based isolation per HubSpot customer) enable secure, scalable vector search across their massive customer base.

**Bazaarvoice -- Product Review Intelligence**
Bazaarvoice processes billions of product reviews across thousands of brands. They use Qdrant to embed and search reviews semantically, enabling features like "find similar complaints across brands" and "match product descriptions to relevant reviews." Qdrant's horizontal scaling handles their data volume, while payload filtering enables brand-level and category-level isolation.

**Bosch -- Industrial IoT and Manufacturing**
Bosch uses Qdrant for anomaly detection in manufacturing processes and semantic search across technical documentation. Sensor readings from factory equipment are embedded and compared against historical patterns to detect anomalies in real-time. Separately, engineers search through millions of technical documents using natural language queries.

**OpenTable -- Restaurant Search and Matching**
OpenTable uses Qdrant to improve restaurant recommendations by embedding diner preferences and restaurant characteristics into a shared vector space. The system considers factors beyond simple cuisine matching: ambiance, price sensitivity, past dining patterns, and occasion type. Qdrant's filtered search ensures recommendations respect constraints like location, availability, and dietary requirements.
