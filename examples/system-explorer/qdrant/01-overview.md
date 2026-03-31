## Overview
<!-- level: beginner -->
<!-- references:
- [Qdrant Official Website](https://qdrant.tech) | official
- [Qdrant GitHub Repository](https://github.com/qdrant/qdrant) | github
- [Qdrant Documentation](https://qdrant.tech/documentation/) | docs
- [About Qdrant](https://qdrant.tech/about-us/) | official
- [Qdrant Series B Announcement](https://www.businesswire.com/news/home/20260312313902/en/) | news
-->

### What Is Qdrant?

Qdrant (pronounced "quadrant") is a high-performance, open-source vector similarity search engine and database built entirely in Rust. It provides a production-ready service with REST and gRPC APIs for storing, searching, and managing vectors alongside rich JSON metadata called payloads.

**One-sentence pitch:** Qdrant turns high-dimensional embeddings into searchable, filterable, production-grade infrastructure so AI applications can find the most semantically similar items in milliseconds, not minutes.

### Who Is It For?

Qdrant is designed for AI and ML engineers building applications that require semantic similarity search at scale. Typical users include:

- **AI application developers** building retrieval-augmented generation (RAG) pipelines
- **Search engineers** implementing semantic or hybrid search systems
- **ML engineers** deploying recommendation engines, anomaly detection, or matching systems
- **Platform teams** needing a dedicated vector database that scales horizontally

### History and Origins

Qdrant was co-founded by **Andrey Vasnetsov** and **Andre Zayarni** in Berlin, Germany. Andrey, while working as Head of Search at a large bank, developed a product recommendation solution based on customer transaction embeddings. Through that experience, he conceived an extension to the HNSW approximate nearest neighbor algorithm that enables metadata-based filtering during graph traversal — a key innovation that would become Qdrant's filterable HNSW.

By mid-2020, Andrey began building a vector search database in Rust as an open-source project. The first working version was officially released on GitHub in May 2021. The choice of Rust was deliberate — it provides memory safety without garbage collection overhead, which is critical for a system that must handle billions of vectors with predictable latency.

Key milestones:
- **2020:** Development begins in Rust
- **May 2021:** First public release on GitHub
- **April 2023:** $7.5M seed funding
- **January 2024:** Qdrant 1.7 introduces sparse vectors and hybrid search
- **2024:** Qdrant Cloud launches on AWS, GCP, and Azure
- **March 2026:** $50M Series B to scale composable vector search as core AI infrastructure; v1.17 released with Gridstore fully replacing RocksDB, and Qdrant Edge for in-process deployments

### Why Rust?

Qdrant is the only major open-source vector database written entirely in Rust. This decision provides:

- **Memory safety without garbage collection** — no unpredictable GC pauses during search
- **Zero-cost abstractions** — high-level code that compiles to bare-metal performance
- **Fearless concurrency** — safe multi-threaded operations guaranteed at compile time
- **Control down to the assembly level** — the team can optimize hot paths precisely

### Key Differentiators

1. **Filterable HNSW** — Qdrant pioneered extending the HNSW graph with payload-aware edges, enabling filtered similarity search without post-filtering accuracy loss
2. **Rich payload filtering** — Full-text, keyword, numeric, geo, datetime, and boolean filters applied during vector search, not after
3. **Multiple vector types** — Dense, sparse, and multi-dense vectors in a single collection for hybrid search
4. **Production distributed architecture** — Raft consensus for metadata, horizontal sharding, configurable replication and consistency levels
5. **Quantization options** — Scalar (4x), product (up to 64x), and binary (32x) quantization to reduce memory footprint
6. **Rust performance** — Predictable latency without GC pauses, efficient memory usage
