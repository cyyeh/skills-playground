## Implementation Details
<!-- level: advanced -->
<!-- references:
- [Qdrant GitHub Repository](https://github.com/qdrant/qdrant) | github
- [Vector Storage Formats (DeepWiki)](https://deepwiki.com/qdrant/qdrant/3.1-vector-storage-formats) | wiki
- [Qdrant 1.13 - GPU Indexing & New Storage Engine](https://qdrant.tech/blog/qdrant-1.13.x/) | blog
- [Scalar Quantization Article](https://qdrant.tech/articles/scalar-quantization/) | official-docs
- [Binary Quantization Article](https://qdrant.tech/articles/binary-quantization/) | official-docs
- [gRPC API Services (DeepWiki)](https://deepwiki.com/qdrant/qdrant/9.2-grpc-api-services) | wiki
-->

### Rust Core

Qdrant is implemented entirely in Rust, leveraging the language's zero-cost abstractions, memory safety guarantees, and performance characteristics. The codebase is organized into several key crates:

- **lib/segment:** The core storage and indexing engine. Contains vector storage implementations, HNSW index builder, payload storage, and field indexes.
- **lib/collection:** Collection management, shard orchestration, optimizer pipeline, and WAL integration.
- **lib/storage:** The top-level TableOfContent, consensus integration, and dispatcher logic.
- **src/:** The main binary entry point, API server setup, and configuration parsing.

Rust's ownership model eliminates data races in the concurrent optimizer pipeline (update worker, optimize worker, flush worker all operating on shared segment state), and the async runtime (tokio) handles thousands of concurrent API connections with minimal overhead.

### Memory-Mapped File Storage

Qdrant's memmap storage uses the `mmap` system call to create a virtual address space backed by disk files. Rather than loading entire vector files into RAM, the operating system's page cache manages which pages are resident in memory.

**How it works:** When a vector is accessed, the OS checks if the corresponding page is in the page cache. If yes (cache hit), the read is as fast as RAM. If not (cache miss), the page is loaded from disk. Frequently accessed vectors naturally stay in cache, while rarely accessed vectors are evicted. This provides an elegant memory management strategy — with abundant RAM, performance equals in-memory storage; with limited RAM, performance degrades gracefully rather than failing.

**HNSW on disk:** The HNSW graph itself can also be memory-mapped (via `hnsw_config.on_disk: true`). Since HNSW traversal accesses a relatively small number of graph nodes per query, the working set stays in page cache even when the full graph does not fit in RAM.

### HNSW Graph Construction

Qdrant's HNSW implementation follows the original algorithm with several optimizations:

**Graph Structure:** The index is a multi-layer graph. Each layer contains a subset of all vectors. Layer 0 contains all vectors. Higher layers contain exponentially fewer vectors, selected randomly with probability `1/m`. Each vector maintains up to `m` bidirectional edges to its nearest neighbors on each layer (2*m on layer 0).

**Construction Algorithm:** For each new vector inserted:
1. The vector enters at the top layer and greedily navigates to the nearest neighbor.
2. At the designated insertion layer (determined by a random level assignment), the vector is connected to its `ef_construct` nearest neighbors.
3. The algorithm descends to layer 0, connecting the vector at each layer.
4. Existing edges are pruned to maintain the maximum `m` edges per node, using heuristic neighbor selection that prefers diverse directional connections.

**Key Parameters:**
- `m` (default: 16): Maximum edges per node. Higher values improve recall but increase memory and build time. Values of 16-64 are typical.
- `ef_construct` (default: 100): Size of the dynamic candidate list during construction. Higher values yield a better-quality graph at the cost of slower indexing.
- `max_indexing_threads`: Number of parallel threads for graph construction. GPU-accelerated indexing was introduced in v1.13 for faster builds.

**Delta Encoding Optimization:** Qdrant compresses HNSW graph link storage using delta encoding — storing differences between sorted neighbor IDs rather than absolute IDs. This reduces memory consumption with minimal CPU overhead for decompression.

**Incremental Building:** The `incremental_hnsw_building` feature flag enables incremental index construction, allowing the HNSW graph to be updated without full rebuilds when small batches of new points arrive.

### Quantization Internals

**Scalar Quantization (int8):** Each float32 dimension is linearly mapped to an int8 value. The mapping is learned from the data distribution: Qdrant computes quantile bounds (e.g., 0.99 quantile to exclude 1% of outliers), then maps the float range to [-128, 127]. Distance calculations on int8 values use SIMD-optimized integer arithmetic, yielding approximately 2x speedup. The `always_ram` option keeps quantized vectors in RAM even when original vectors use memmap.

**Binary Quantization (1-bit):** Each float32 dimension is converted to a single bit: 1 if positive, 0 if zero or negative. Distance computation uses XOR followed by popcount — hardware-accelerated CPU instructions that operate on 64 bits simultaneously. This yields up to 40x speedup with 32x memory compression. Works best with high-dimensional embeddings (>1024 dimensions) from models that produce well-distributed component values. Qdrant v1.15 introduced 1.5-bit and 2-bit variants that explicitly handle near-zero values for better accuracy.

**Product Quantization:** Vectors are divided into sub-vectors (chunks), and each chunk is independently quantized using k-means clustering with 256 centroids. Each sub-vector is replaced by an 8-bit centroid index. Compression ratios up to 64x are possible, but the approach is not SIMD-friendly and incurs significant accuracy loss (~0.7 recall). Best suited for extremely memory-constrained environments with high-dimensional vectors.

**Rescoring Pipeline:** During quantized search, Qdrant first retrieves candidates using the compressed vectors (fast but approximate). It then retrieves the original float32 vectors for the top candidates and recomputes exact distances. The `oversampling` parameter controls how many extra candidates are retrieved (e.g., 2.0 means retrieve 2x the requested limit, then rescore and return top-k).

### gRPC and REST API Design

The API layer is organized into distinct services, each handling specific aspects:

- **Collections Service:** Collection lifecycle (create, update, delete, list, info). Defined in `collections.proto`.
- **Points Service:** Vector and payload CRUD operations (upsert, delete, get, scroll, search, recommend, discover). The most frequently used service. Defined in `points.proto`.
- **Snapshots Service:** Snapshot creation, listing, download, and recovery.
- **Cluster Service:** Cluster status, peer management, and shard operations.

REST uses actix-web with JSON serialization. gRPC uses tonic with Protocol Buffer serialization. Both are auto-generated from the same protobuf definitions, ensuring consistency. The REST API also serves an OpenAPI specification for client generation.

### Storage Format Evolution

Qdrant has evolved its storage backend over time:

- **RocksDB era:** Early versions used RocksDB for both payload storage and structured metadata. RocksDB provides crash-safe key-value storage with good read/write performance.
- **GridStore (v1.13+):** A custom block-based key-value storage engine designed as a RocksDB replacement. GridStore is optimized for Qdrant's specific access patterns — particularly the mix of random reads (payload lookups) and sequential writes (batch upserts). The `payload_index_skip_rocksdb` feature flag controls the migration path.
- **Vector files:** Vector data is stored in flat binary files (sequential float32 arrays for dense vectors) or memory-mapped files, separate from the key-value store. This separation allows independent optimization of vector access patterns.
