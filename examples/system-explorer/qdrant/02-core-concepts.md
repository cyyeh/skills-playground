## Core Concepts
<!-- level: beginner -->
<!-- references:
- [Qdrant Documentation Overview](https://qdrant.tech/documentation/overview/) | docs
- [Fundamentals of Qdrant: 6 Core Concepts](https://airbyte.com/data-engineering-resources/fundamentals-of-qdrant) | tutorial
- [Points, Vectors and Payloads](https://qdrant.tech/course/essentials/day-1/embedding-models/) | course
- [HNSW Indexing Fundamentals](https://qdrant.tech/course/essentials/day-2/what-is-hnsw/) | course
- [Combining Vector Search and Filtering](https://qdrant.tech/course/essentials/day-2/filterable-hnsw/) | course
- [Sparse Vectors and Inverted Indexes](https://qdrant.tech/course/essentials/day-3/sparse-vectors/) | course
-->

### The Building Blocks of Vector Search

Qdrant is built on seven core concepts. Understanding them gives you the vocabulary to reason about how semantic search works, why certain queries are fast or slow, and how to structure your data for optimal retrieval.

---

### 1. Collections

**Definition:** A collection is a named set of points that share the same vector configuration. It is the top-level organizational unit in Qdrant, analogous to a table in a relational database.

**Analogy:** Think of a collection as a filing cabinet. All folders (points) in the cabinet have the same structure — same number of dimensions for their vectors, same distance metric. You can have one cabinet for product embeddings and another for user embeddings.

**Why it matters:** When you create a collection, you define the vector size, distance metric (cosine, dot product, Euclidean, or Manhattan), and optional parameters like HNSW configuration and quantization. These choices are fixed for the collection's lifetime and directly affect search speed and accuracy.

---

### 2. Points

**Definition:** A point is the fundamental unit of data in Qdrant. Each point consists of a unique ID (64-bit integer or UUID), one or more vectors, and an optional JSON payload containing metadata.

**Analogy:** Imagine a pin on a map. The pin's position represents the vector (where it sits in high-dimensional space), the pin's label is the ID, and a sticky note attached to it is the payload with extra information like name, category, or price.

**Why it matters:** Points are what you search through. When you perform a similarity search, Qdrant finds the points whose vectors are closest to your query vector, then returns their IDs and payloads. The richer your payloads, the more you can filter and contextualize results.

---

### 3. Vectors

**Definition:** Vectors are fixed-length arrays of floating-point numbers that represent data in high-dimensional space. Qdrant supports three types:

- **Dense vectors** — Traditional embeddings from models like OpenAI, Cohere, or sentence-transformers. Every dimension has a value. These capture semantic meaning.
- **Sparse vectors** — Only non-zero dimensions are stored (like BM25, SPLADE, or miniCOIL outputs). Efficient for keyword-style lexical matching.
- **Multi-dense vectors (multivectors)** — A list of dense vectors treated as a single entity. Used for late-interaction models like ColBERT, where each token gets its own embedding.

Qdrant also supports **named vectors**, allowing multiple vector spaces per point. For example, a product might have a text embedding and an image embedding stored as separate named vectors in the same point.

**Analogy:** Dense vectors are like GPS coordinates — every dimension contributes to the position. Sparse vectors are like a shopping list — only the items you need are listed, everything else is zero. Multivectors are like a fingerprint — multiple ridges (token embeddings) that together identify the whole.

**Why it matters:** The vector type determines search behavior. Dense vectors excel at semantic understanding, sparse vectors preserve exact keyword matches, and combining them enables hybrid search that captures both meaning and precise terms.

---

### 4. Payloads

**Definition:** Payloads are arbitrary JSON objects attached to points, storing metadata like category names, prices, dates, geographic coordinates, or any structured information relevant to your data.

**Analogy:** If the vector is the "where" (position in meaning-space), the payload is the "what" — all the business context that makes a search result useful.

**Why it matters:** Payloads enable filtered search. Instead of searching all 10 million vectors, you can search only vectors where `category = "electronics"` and `price < 100`. Qdrant indexes payload fields you specify, enabling these filters to run efficiently during the HNSW graph traversal rather than as a post-processing step.

Supported payload types include: keywords, integers, floats, booleans, text (full-text indexed), geo points, datetime, and UUIDs.

---

### 5. Filtering

**Definition:** Filtering narrows the search space based on payload conditions before or during vector similarity computation. Qdrant supports `must`, `should`, `must_not` clauses (similar to Elasticsearch), as well as range, geo-radius, full-text match, and nested filters.

**Analogy:** Filtering is like telling a librarian: "Find me the books most similar in theme to this one, but only look in the science fiction section published after 2020." The librarian doesn't search the entire library — they go straight to the right shelves.

**Why it matters:** In production, almost every vector search involves filters. "Find similar products in this category," "find matching resumes in this region," "find related articles from this year." Qdrant's filterable HNSW ensures that filtered searches remain fast by building filter-aware graph edges, rather than searching first and filtering after — which can discard most results and return poor-quality matches.

---

### 6. HNSW Index

**Definition:** Hierarchical Navigable Small World (HNSW) is Qdrant's primary vector index. It organizes vectors into a multi-layered graph where higher layers contain coarse, long-range connections and lower layers contain fine-grained, local connections.

**Analogy:** Imagine navigating a city. First you take a highway (top layer) to get near your destination quickly, then switch to main roads (middle layers), then side streets (bottom layer) to reach the exact address. Each layer provides progressively finer navigation, and you never need to check every single street in the city.

**Why it matters:** HNSW reduces similarity search from O(N) brute-force scans to approximately O(log N) graph traversals. The key tuning parameters are:

- **m** — Maximum edges per node (typically 16-64). Higher values improve recall but use more memory.
- **ef_construct** — Candidate list size during index building. Higher values produce a better graph but slower builds.
- **ef** (at query time) — Candidate list size during search. Higher values improve recall at the cost of latency.

Qdrant extends standard HNSW with **filterable HNSW**, which adds extra edges to maintain graph connectivity when filters exclude large portions of the graph. This is Qdrant's key algorithmic innovation.

---

### 7. Quantization

**Definition:** Quantization compresses vector representations to reduce memory usage and speed up distance calculations, at a controlled cost to search accuracy.

Qdrant supports three quantization methods:
- **Scalar quantization** — Converts 32-bit floats to 8-bit integers (4x compression)
- **Product quantization (PQ)** — Divides vectors into subvectors and quantizes each independently (4x to 64x compression)
- **Binary quantization** — Compresses each dimension to a single bit (32x compression)

**Analogy:** Quantization is like reducing the resolution of an image. A 4K photo and a 720p version show the same scene, but the compressed version takes far less storage and loads faster. You trade some fine detail for massive efficiency gains.

**Why it matters:** At scale, vectors dominate memory usage. A collection of 100 million 768-dimensional vectors requires ~286 GB of RAM at full precision. With scalar quantization that drops to ~72 GB; with binary quantization, ~9 GB. Quantization makes billion-scale deployments economically viable while maintaining 95-99% of full-precision search quality.
