## Core Concepts
<!-- level: beginner -->
<!-- references:
- [Qdrant Concepts Documentation](https://qdrant.tech/documentation/manage-data/) | official-docs
- [The Fundamentals of Qdrant](https://airbyte.com/data-engineering-resources/fundamentals-of-qdrant) | blog
- [HNSW Indexing Fundamentals](https://qdrant.tech/course/essentials/day-2/what-is-hnsw/) | official-docs
- [Vector Quantization Methods](https://qdrant.tech/documentation/manage-data/quantization/) | official-docs
-->

### Vectors & Embeddings

**Definition:** A vector (or embedding) is a list of floating-point numbers that represents a piece of data — a sentence, an image, a product, a user profile — in a high-dimensional space. These vectors are produced by machine learning models (like OpenAI's text-embedding-ada-002 or sentence-transformers) that learn to place similar items close together in this space.

**Analogy:** Imagine every book in a library placed on a vast map where proximity represents similarity. Cookbooks cluster near each other, sci-fi novels group together, and a cookbook about science fiction cuisine sits between the two clusters. Vectors are the GPS coordinates on this map.

**Why it matters:** Vectors are the fundamental data type in Qdrant. Every search query starts with a vector, and Qdrant's job is to find the stored vectors that are closest to it. The quality of your search results depends on the quality of your embedding model, but Qdrant ensures the retrieval is fast and accurate.

### Points

**Definition:** A point is the atomic unit of data in Qdrant. Each point consists of three parts: a unique identifier (64-bit integer or UUID), one or more vectors, and an optional JSON payload containing metadata. Points are what you insert, update, search for, and delete.

**Analogy:** Think of a point as a library card. The ID is the card number, the vector is the "location on the similarity map" where the book belongs, and the payload is all the extra information written on the card — title, author, genre, publication year.

**Why it matters:** Points are the records you interact with through the API. When you upsert data, you are creating points. When you search, Qdrant returns the points whose vectors are most similar to your query vector. The payload on each point enables rich filtering without a separate metadata database.

### Collections

**Definition:** A collection is a named group of points that share the same vector configuration — dimensionality and distance metric. All vectors within a collection must have the same number of dimensions and are compared using the same similarity function. Collections are the top-level organizational unit.

**Analogy:** A collection is like a filing cabinet where every folder uses the same labeling system. You would not mix folders labeled by Dewey Decimal with folders labeled by Library of Congress — similarly, you would not mix 384-dimensional vectors with 1536-dimensional vectors in the same collection.

**Why it matters:** Collections define the schema for your vector data. When you create a collection, you choose the vector size (e.g., 1536 for OpenAI embeddings) and the distance metric (cosine, dot product, Euclidean, or Manhattan). This configuration determines how similarity is calculated for every search.

### Payloads

**Definition:** A payload is arbitrary JSON metadata attached to a point. Payloads can contain strings, numbers, booleans, arrays, nested objects, geo-coordinates, and datetime values. Payload fields can be indexed for efficient filtering during search.

**Analogy:** If a vector tells you where an item sits on the similarity map, the payload is the item's detailed profile card — its category, price, creation date, language, author, and any other structured attribute you want to filter on.

**Why it matters:** Payloads enable filtered vector search, which is one of Qdrant's standout features. Instead of just finding the 10 most similar items globally, you can find the 10 most similar items that are also in the "electronics" category, priced under $50, and published after 2024. This combination of semantic similarity and structured filtering is essential for real-world applications.

### HNSW Index

**Definition:** Hierarchical Navigable Small World (HNSW) is the primary indexing algorithm Qdrant uses for approximate nearest neighbor (ANN) search. It builds a multi-layered graph where each node is a vector, and edges connect nearby vectors. Upper layers contain fewer nodes with long-range connections for fast navigation; lower layers contain all nodes with short-range connections for precision.

**Analogy:** Imagine navigating a city to find the closest coffee shop. At the highway level (top layer), you quickly drive to the right neighborhood. At the street level (middle layer), you navigate to the right block. At the sidewalk level (bottom layer), you walk to the exact shop. HNSW does this with vectors — it starts with coarse global navigation and progressively refines to precise local search.

**Why it matters:** Brute-force comparison of a query vector against millions of stored vectors would be too slow. HNSW provides sub-linear search time — typically O(log n) — while maintaining high recall (usually 95-99%+). The trade-off is that it uses more memory for the graph structure and is an approximate algorithm, but in practice the accuracy loss is negligible for most applications.

### Quantization

**Definition:** Quantization is a technique that compresses vector representations to reduce memory usage and speed up distance calculations. Qdrant supports three methods: Scalar Quantization (float32 to int8, 4x compression), Binary Quantization (float32 to 1-bit, 32x compression), and Product Quantization (divides vectors into sub-vectors, up to 64x compression).

**Analogy:** Think of quantization like reducing image resolution. A 4K photo (float32 vectors) is beautiful but takes a lot of storage. A compressed JPEG (scalar quantization) looks almost identical at a fraction of the size. A thumbnail (binary quantization) is much smaller and you can scan through thousands instantly, though you might want to double-check the full image for your final picks.

**Why it matters:** At scale, vector storage dominates memory costs. A collection of 10 million 1536-dimensional float32 vectors requires about 57 GB of RAM. With scalar quantization, that drops to ~14 GB. With binary quantization, it drops to ~1.8 GB. Quantization makes it practical to serve billion-scale vector collections on reasonable hardware, and Qdrant's rescoring mechanism (re-evaluating top candidates with original vectors) keeps accuracy high.

### Filtering

**Definition:** Filtering in Qdrant applies structured conditions on payload fields during vector search. Conditions include keyword match, numeric range, geo-radius, full-text search, datetime ranges, and nested field access. Filters use boolean logic with must, should, and must_not clauses.

**Analogy:** Filtering is like adding WHERE clauses to a SQL query. Vector search alone is "find me similar items." Filtered vector search is "find me similar items WHERE category = 'shoes' AND price < 100 AND color IN ('red', 'blue')."

**Why it matters:** Real-world search applications almost always need filtering. A RAG system needs to filter by document source or date. A recommendation engine needs to filter by user region or product availability. Qdrant's filters are applied efficiently during the HNSW traversal (not as a post-processing step), which means filtering does not significantly degrade search performance.

### Distance Metrics

**Definition:** A distance metric defines how similarity between two vectors is calculated. Qdrant supports four metrics: Cosine (angular similarity, ignores magnitude), Dot Product (accounts for both direction and magnitude), Euclidean (straight-line distance in vector space), and Manhattan (grid-based distance, robust to outliers).

**Analogy:** Choosing a distance metric is like choosing how to measure the "closeness" of two cities. Euclidean distance is straight-line (as the crow flies). Manhattan distance follows the road grid. Cosine similarity measures the angle of the direction you would travel, ignoring how far away the cities are.

**Why it matters:** The choice of distance metric must match your embedding model's training objective. Most text embedding models (OpenAI, Cohere, sentence-transformers) are trained with cosine similarity. Some models produce normalized vectors where dot product and cosine are equivalent. Choosing the wrong metric will produce poor search results even with a good model.

### How They Fit Together

When you use Qdrant, you first create a collection specifying the vector dimensionality and distance metric. You then upsert points, each containing a unique ID, one or more vectors (produced by your embedding model), and a JSON payload with metadata. Qdrant stores the vectors and builds an HNSW index graph connecting similar vectors across multiple layers. If you enable quantization, compressed copies of the vectors are created for fast initial distance calculations. When a search query arrives, Qdrant navigates the HNSW graph from the top layer down, progressively narrowing the candidate set. If you include payload filters, Qdrant applies them during the graph traversal using indexed payload fields, efficiently skipping points that do not match your criteria. The top candidates are optionally rescored against the original uncompressed vectors, and the final ranked results — complete with IDs, scores, and payloads — are returned through the REST or gRPC API.
