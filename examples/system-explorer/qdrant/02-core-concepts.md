## Core Concepts
<!-- level: beginner -->
<!-- references:
- [Qdrant Concepts Documentation](https://qdrant.tech/documentation/concepts/) | official-docs
- [The Fundamentals of Qdrant: Understanding the 6 Core Concepts](https://airbyte.com/data-engineering-resources/fundamentals-of-qdrant) | blog
- [HNSW Indexing Fundamentals - Qdrant Essentials Course](https://qdrant.tech/course/essentials/day-2/what-is-hnsw/) | official-docs
- [Combining Vector Search and Filtering - Qdrant](https://qdrant.tech/course/essentials/day-2/filterable-hnsw/) | official-docs
-->

### Collections

**Definition:** A collection is Qdrant's primary organizational unit -- a named container that holds a set of points (vectors + metadata) with a shared configuration. Each collection defines the vector dimensionality, distance metric, HNSW parameters, and quantization settings that apply to all points within it.

**Analogy:** Think of a collection like a filing cabinet drawer with a specific label. The drawer has fixed dimensions (vector size), a specific sorting method (distance metric), and organizational rules (indexing parameters). Everything you put into that drawer must conform to its structure. You might have one drawer for "product embeddings" and another for "user profile embeddings" -- each configured differently.

**Why it matters:** Collections are the unit of configuration, sharding, and replication. When you create a collection, you decide the fundamental trade-offs for all data in it: how accurate vs. how fast searches should be (HNSW parameters `m` and `ef_construct`), how much memory to use (quantization), and how many replicas to maintain for fault tolerance. Choosing these parameters correctly at collection creation time determines the performance characteristics of every search against that data.

### Points

**Definition:** A point is the fundamental data record in Qdrant. Each point consists of three parts: a unique ID (64-bit integer or UUID), one or more vectors (the numerical embeddings), and an optional payload (JSON metadata). Points are the things you search for and retrieve.

**Analogy:** Imagine a library card catalog entry. Each card has a unique catalog number (ID), a location code that tells you where the book sits on the shelves (vector -- its position in embedding space), and descriptive information like title, author, and genre (payload). When you search for similar books, you're comparing location codes; when you filter, you're checking the descriptive information.

**Why it matters:** Points are the atomic unit of storage and search. Every upsert, delete, search hit, and filter evaluation operates on points. The separation of vector data from payload data is a deliberate design choice -- vectors are stored in optimized formats (including quantized representations) for fast distance computation, while payloads are stored and indexed separately for efficient filtering.

### Vectors

**Definition:** A vector is a fixed-length array of floating-point numbers that represents the semantic meaning of a piece of data. Qdrant supports dense vectors (traditional embeddings), sparse vectors (for lexical or BM25-style matching), and multi-vectors (ColBERT-style late interaction embeddings). A single point can hold multiple named vectors.

**Analogy:** Think of a vector as GPS coordinates, but in hundreds or thousands of dimensions instead of two. Just as GPS coordinates encode a physical location so you can find nearby places, embedding vectors encode semantic meaning so you can find similar concepts. Two restaurant reviews with similar sentiment will have vectors that are "close together" in this high-dimensional space, even if they use completely different words.

**Why it matters:** The quality and dimensionality of your vectors determine everything about search quality. Qdrant is agnostic to how vectors are produced -- it works with any embedding model (OpenAI, Cohere, sentence-transformers, CLIP, etc.). The database supports multiple distance metrics (Cosine, Euclidean, Dot Product, Manhattan) because different embedding models require different similarity measures. Named vectors allow a single point to be searchable from multiple perspectives (e.g., a product with both a text embedding and an image embedding).

### Payloads

**Definition:** A payload is a JSON object attached to a point containing arbitrary metadata -- strings, integers, floats, booleans, arrays, nested objects, geo-coordinates, and datetimes. Payload fields can be indexed to enable efficient filtered search.

**Analogy:** If vectors are the GPS coordinates of a restaurant, payloads are the Yelp listing details -- cuisine type, price range, hours, ratings, location. When you search for "restaurants near me," the vector finds semantically similar places, and the payload filter narrows results to "Italian, under $30, open now." Without payload filtering, you'd get every nearby restaurant regardless of your preferences.

**Why it matters:** Real-world search almost always combines semantic similarity with structured filtering. Qdrant's payload indexing system supports keyword match, full-text search, numeric range, geo-bounding box, and nested field conditions. The crucial innovation is that Qdrant integrates filtering directly into the HNSW graph traversal rather than applying it as a separate post-processing step, which preserves search quality even when filters are highly selective.

### HNSW Index

**Definition:** HNSW (Hierarchical Navigable Small World) is the graph-based approximate nearest neighbor algorithm at the heart of Qdrant's search engine. It builds a multi-layer graph where each point connects to its nearest neighbors, creating a structure that can be traversed in O(log N) time to find approximate nearest neighbors.

**Analogy:** Imagine a city where you need to find a specific coffee shop. Instead of checking every shop in the city (brute-force), you use a hierarchical social network. At the top level, you ask a well-connected friend who knows people across the whole city -- they point you to the right neighborhood. At the next level, you ask someone who knows that neighborhood well -- they point you to the right block. At the bottom level, you ask a local who knows every shop on the block. Each level narrows your search, and you only visit a handful of "people" (nodes) out of millions.

**Why it matters:** HNSW is what makes Qdrant fast. Without it, finding the nearest vectors to a query would require computing distances to every single point -- impossibly slow for millions or billions of vectors. HNSW's key parameters are `m` (how many connections each node maintains -- more connections = better recall but more memory), `ef_construct` (how thoroughly the graph is built -- higher = better graph quality but slower indexing), and `ef` (search beam width at query time -- higher = better recall but slower queries). Qdrant extends standard HNSW with filter-aware graph construction, ensuring the graph remains navigable even when filters exclude large portions of points.

### Segments

**Definition:** A segment is Qdrant's internal storage unit -- a self-contained partition of a collection's data that holds its own vectors, payloads, indexes, and ID mappings. Collections consist of multiple segments that are managed transparently by the optimizer.

**Analogy:** Think of segments like chapters in a book that's being written. New data goes into the current "appendable" chapter (an unindexed segment optimized for writes). Periodically, the optimizer "publishes" completed chapters by building HNSW indexes and applying quantization (creating non-appendable, optimized segments). Old chapters may be merged together to reduce overhead. The reader (search engine) searches all chapters in parallel and merges results.

**Why it matters:** Segments enable Qdrant to handle concurrent reads and writes without blocking. New writes go to an appendable segment while searches proceed against already-indexed segments. The optimizer runs in the background, merging small segments, building indexes, and applying quantization -- all without interrupting queries. This segment-based architecture is also the foundation for sharding: when a collection is distributed across nodes, each shard is essentially a set of segments managed locally.

### How They Fit Together

When you upsert a point into Qdrant, the point (ID + vector + payload) is written to the write-ahead log (WAL) of the local shard, then inserted into the current appendable segment. The payload is stored and optionally indexed by the `StructPayloadIndex`. In the background, the optimizer monitors segment sizes and triggers merges: it combines small segments, builds HNSW graphs over the merged vector data, and applies quantization to reduce memory usage. When you execute a search, Qdrant's query planner determines the optimal strategy per segment based on the filter's selectivity: for broad filters, it traverses the HNSW graph and skips non-matching nodes during traversal; for highly selective filters, it retrieves matching point IDs from the payload index and performs a linear scan of just those vectors. Results from all segments (and all shards, in distributed mode) are merged and ranked by similarity score, and the top-k results are returned with their payloads.
