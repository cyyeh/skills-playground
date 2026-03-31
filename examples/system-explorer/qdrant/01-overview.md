## Overview
<!-- level: beginner -->
<!-- references:
- [Qdrant Official Documentation](https://qdrant.tech/documentation/) | official-docs
- [Qdrant GitHub Repository](https://github.com/qdrant/qdrant) | github
- [Qdrant 2025 Recap](https://qdrant.tech/blog/2025-recap/) | blog
-->

Qdrant (pronounced "quadrant") is an open-source vector similarity search engine and database built in Rust, designed to store, index, and query high-dimensional vectors at scale. Think of it as a specialized database that understands "similarity" rather than exact matches — instead of asking "give me the row where id = 42," you ask "give me the items most similar to this one."

Created by Andrey Vasnetsov and the Qdrant team, the project was born from the growing need for a production-grade vector database that could handle the demands of modern AI applications — particularly retrieval-augmented generation (RAG), semantic search, and recommendation systems — without sacrificing performance, filtering flexibility, or operational simplicity.

### What It Is

Qdrant is a vector similarity search engine that stores vectors (numerical representations of data produced by machine learning models) alongside rich JSON metadata called payloads. It provides blazing-fast approximate nearest neighbor (ANN) search using an HNSW index, combined with powerful payload filtering that lets you narrow results by structured criteria. You can run it as a Docker container, a standalone binary, or as a managed cloud service.

### Who It's For

Qdrant is built for AI/ML engineers, backend developers, and data scientists who need to power applications with similarity search. It is ideal for teams building RAG pipelines for LLM applications, semantic search engines, recommendation systems, image similarity search, or anomaly detection workflows. Its Rust foundation makes it particularly suited for production deployments where performance and memory efficiency matter.

### The One-Sentence Pitch

Qdrant gives you a production-ready vector database written in Rust that combines high-performance approximate nearest neighbor search with rich payload filtering, quantization for memory efficiency, and distributed deployment — all through simple REST and gRPC APIs.
