## Core Concepts
<!-- level: beginner -->
<!-- references:
- [Qdrant Concepts Documentation](https://qdrant.tech/documentation/overview/) | official-docs
- [Points, Vectors and Payloads](https://qdrant.tech/course/essentials/day-1/embedding-models/) | official-docs
- [The Fundamentals of Qdrant](https://airbyte.com/data-engineering-resources/fundamentals-of-qdrant) | blog
- [Understanding Vector Search in Qdrant](https://qdrant.tech/documentation/overview/vector-search/) | official-docs
-->

### Collections

A **Collection** is a named container for vectors and their associated data -- like a filing cabinet dedicated to one type of document. Each collection defines the dimensionality of its vectors, the distance metric used for comparison (cosine, Euclidean, dot product, or Manhattan), and the indexing and storage configuration. You might have one collection for product embeddings, another for customer support ticket embeddings, and a third for image feature vectors. Collections are the top-level organizational unit: all search, insert, and management operations are scoped to a single collection.

*Analogy:* Think of a collection as a dedicated photo album. Every photo in the album has the same dimensions (say, 4x6 inches) and is organized by the same sorting rule (chronological, by color palette, etc.). You would not mix passport photos with panoramic landscapes in the same album because the dimensions and sorting criteria differ.

### Points

A **[Point](https://qdrant.tech/documentation/manage-data/points/)** is the fundamental record in Qdrant -- a bundle of a unique ID, one or more vectors, and an optional payload. The name "point" comes from the geometric interpretation: each vector places the record at a specific location in high-dimensional space, and similarity search finds the points closest to a query.

*Analogy:* A point is like a pin on a map. The pin's location (its vector) tells you where it sits in space, the label on the pin (its ID) uniquely identifies it, and the sticky note attached to it (its payload) carries extra information like "this is a coffee shop, open until 10pm, rating 4.5."

### Vectors

A **Vector** is the numerical representation of your data -- an array of floating-point numbers produced by an embedding model. Qdrant supports [dense vectors](https://qdrant.tech/documentation/overview/vector-search/) (hundreds to thousands of dimensions, capturing semantic meaning), sparse vectors (high-dimensional but mostly zeros, good for keyword-style matching), and multivectors (multiple vector representations per point, used with late-interaction models like ColBERT). Dense and sparse vectors can be combined in hybrid search for the best of both worlds.

*Analogy:* A vector is like a DNA fingerprint for your data. Just as DNA encodes biological traits into a sequence of nucleotides, an embedding model encodes the meaning of a document, image, or audio clip into a sequence of numbers. Two pieces of data with similar "DNA" (close vectors) are semantically similar, even if their surface forms look different.

### Payloads

A **[Payload](https://qdrant.tech/documentation/manage-data/payload/)** is the structured metadata attached to a point -- a JSON object containing arbitrary key-value pairs such as categories, prices, dates, tags, or nested objects. Payloads are stored separately from vectors and can be indexed for efficient filtering. This is what makes Qdrant more than a pure vector index: you can search for "the 10 most similar products" AND simultaneously filter to "only products under $50 in the electronics category."

*Analogy:* If a vector is the DNA fingerprint, the payload is the medical chart. The fingerprint identifies who someone is; the chart carries structured details like blood type, allergies, and medications. When a doctor searches for matching donors, they use both -- similarity of the fingerprint AND specific criteria from the chart.

### HNSW Index

The **[HNSW (Hierarchical Navigable Small World)](https://qdrant.tech/course/essentials/day-2/what-is-hnsw/)** index is the core data structure that makes vector search fast. Instead of comparing a query against every single vector (brute-force), HNSW builds a multi-layered graph where each vector is a node connected to its nearest neighbors. The top layers are sparse (few nodes, long-range connections for fast navigation), and the bottom layers are dense (all nodes, fine-grained connections for precision). Search starts at the top and "zooms in" through the layers -- delivering approximate nearest neighbors in logarithmic time.

*Analogy:* HNSW works like navigating a city using progressively detailed maps. You start with a country map (sparse top layer) to identify the right region, switch to a city map (middle layer) to find the neighborhood, then use a street map (dense bottom layer) to find the exact address. Each map level narrows your search area dramatically, so you never have to scan every street in the country.

### Segments

A **Segment** is Qdrant's internal storage unit -- a self-contained partition of a collection's data with its own vector storage, payload storage, and index. Rather than maintaining one monolithic HNSW graph (which would become prohibitively expensive to update), Qdrant breaks data into segments: mutable segments that accept new writes quickly, and immutable segments that have been optimized with a full HNSW index. A background optimizer periodically merges and compacts segments.

*Analogy:* Segments are like chapters in a book that is being written. New content goes into the current "draft chapter" (mutable segment) where it can be quickly added and edited. Once a chapter reaches a certain length, it gets "published" (converted to an immutable segment with a proper index), making it fast to search but no longer directly editable. The table of contents (segment metadata) lets you know which chapters to search.

### Quantization

**[Quantization](https://qdrant.tech/documentation/manage-data/quantization/)** is a compression technique that reduces the memory footprint of vectors by lowering their numerical precision. Qdrant supports three methods: scalar quantization (float32 to int8, ~4x compression), product quantization (divides vectors into sub-vectors and codebook-encodes them, 4-64x compression), and binary quantization (each dimension becomes a single bit, ~32x compression with up to [40x speed improvement](https://qdrant.tech/articles/binary-quantization/)). The compressed vectors live in RAM for fast approximate scoring, while full-precision originals can be stored on disk for re-ranking.

*Analogy:* Quantization is like creating thumbnail versions of high-resolution photographs. The thumbnails (quantized vectors) take far less space and can be browsed quickly to find candidates, but when you need to examine details, you pull up the full-resolution original (the uncompressed vector on disk) for a precise comparison.

### How They Fit Together

The data flow through Qdrant's core concepts follows a clear path. You create a **Collection** with a defined vector configuration. You insert **Points**, each carrying one or more **Vectors** (the numerical embedding of your data) and an optional **Payload** (structured metadata). Under the hood, points land in a mutable **Segment**, where they are immediately searchable via a simple scan. As segments accumulate data, the optimizer converts them to immutable segments with a full **HNSW Index** for fast approximate search. **Quantization** can be enabled to compress vectors in RAM, reducing memory usage while keeping search fast. When you issue a search query, Qdrant's query planner fans out across segments, uses the HNSW graph to find approximate nearest neighbors, applies payload filters either during or after graph traversal, and merges results into a ranked list. In a distributed setup, this same process happens across shards (each containing their own segments) on multiple nodes, with results merged at the coordinator.
