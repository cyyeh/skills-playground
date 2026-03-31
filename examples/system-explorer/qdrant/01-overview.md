## Overview
<!-- level: beginner -->
<!-- references:
- [Qdrant Documentation Overview](https://qdrant.tech/documentation/overview/) | official-docs
- [What is a Vector Database?](https://qdrant.tech/articles/what-is-a-vector-database/) | blog
- [Qdrant 2025 Recap: Powering the Agentic Era](https://qdrant.tech/blog/2025-recap/) | blog
-->

Qdrant (pronounced "quadrant") is an open-source vector similarity search engine and database, purpose-built for the AI era. While traditional databases excel at finding exact matches -- "give me the user with ID 42" -- Qdrant answers a fundamentally different question: "give me the things most similar to this." It stores high-dimensional vectors (numerical representations of data produced by machine learning models) and retrieves the nearest neighbors with sub-millisecond latency, even across billions of vectors.

Founded in 2021 in Berlin, Qdrant is written entirely in [Rust](https://www.rust-lang.org/) with a custom storage engine called Gridstore, SIMD-accelerated distance computations, and a layered segment architecture. It exposes both [REST and gRPC APIs](https://qdrant.tech/documentation/overview/), supports rich payload filtering alongside vector search, and scales horizontally with built-in sharding and replication. In March 2026, Qdrant [raised a $50 million Series B](https://www.businesswire.com/news/home/20260312313902/en/Qdrant-Raises-50-Million-Series-B-to-Define-Composable-Vector-Search-as-Core-Infrastructure-for-Production-AI) to define composable vector search as core infrastructure for production AI, with enterprises like Tripadvisor, HubSpot, OpenTable, and Bosch relying on it in production.

### What It Is

Qdrant is a vector database and similarity search engine -- like a librarian with a photographic memory who, instead of organizing books by title or author, understands the meaning of every book and can instantly find the ones most relevant to your question. You give it vectors (dense or sparse numerical representations produced by embedding models), attach structured metadata called "payloads," and Qdrant finds the closest matches using an optimized HNSW graph index while simultaneously filtering on your metadata conditions.

### Who It's For

Qdrant is built for AI/ML engineers, backend developers, and platform teams who need production-grade similarity search. If you are building retrieval-augmented generation (RAG) pipelines, recommendation engines, image or audio search, anomaly detection, or any system where "find the most similar" is a core operation, Qdrant is designed for your workload. It particularly suits teams that want full control over their infrastructure -- whether self-hosted, on-premises, or across hybrid/private cloud deployments -- without sacrificing the performance and developer experience of a managed service.

### The One-Sentence Pitch

Qdrant is a Rust-native vector database that gives your AI applications fast, filtered similarity search at any scale -- from a laptop prototype to a billion-vector production cluster -- with the reliability and performance guarantees that come from a purpose-built engine rather than a bolt-on index.
