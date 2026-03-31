## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [Qdrant Integrations Partners](https://qdrant.tech/partners/) | official-docs
- [LangChain Integration](https://qdrant.tech/documentation/frameworks/langchain/) | official-docs
- [LlamaIndex Integration](https://qdrant.tech/documentation/frameworks/llama-index/) | official-docs
- [Qdrant GitHub Organization](https://github.com/qdrant) | github
-->

### Official Tools & Extensions

**Client SDKs (GA, actively maintained):**
- **[Python SDK](https://github.com/qdrant/qdrant-client)** -- The most feature-complete client. Supports sync/async operations, local in-memory mode for testing (`:memory:`), and automatic batching. Installable via `pip install qdrant-client`.
- **[JavaScript/TypeScript SDK](https://github.com/qdrant/qdrant-js)** -- Full REST and gRPC support for Node.js and browser environments. Installable via `npm install @qdrant/js-client-rest`.
- **[Rust SDK](https://github.com/qdrant/rust-client)** -- Native Rust client using gRPC via Tonic. Provides the tightest integration for Rust-based applications.
- **[Go SDK](https://github.com/qdrant/go-client)** -- gRPC-based client for Go services.
- **[Java SDK](https://github.com/qdrant/java-client)** -- gRPC-based client for JVM applications.
- **[.NET SDK](https://github.com/qdrant/qdrant-dotnet)** -- gRPC-based client for C#/.NET applications.

**Qdrant Cloud** -- Fully managed deployment with automatic scaling, monitoring, and backups. Supports dedicated clusters in AWS, GCP, and Azure. Includes a free tier for development. The Cloud API is [Terraform-enabled](https://qdrant.tech/blog/2025-recap/) for infrastructure-as-code workflows.

**Qdrant Cloud Inference** -- A managed embedding service that unifies vector generation and storage. Send raw text or images, and the service handles embedding generation, vector storage, and search in a single API call -- eliminating the need to manage separate embedding model deployments.

**Qdrant Edge** -- Extends Qdrant's retrieval capabilities to edge devices (mobile, IoT, local workstations) for low-latency, privacy-preserving search without server dependency. Useful for offline-capable applications and on-device AI agents.

**Web Dashboard** -- Built-in UI at `http://localhost:6333/dashboard` for browsing collections, inspecting points, running test queries, and monitoring cluster health. No additional deployment required -- it ships with the Qdrant binary.

**Helm Chart** -- Official [Kubernetes Helm chart](https://github.com/qdrant/qdrant-helm) for deploying Qdrant clusters on Kubernetes with configurable replicas, persistent volumes, and resource limits.

### Community Ecosystem

**LLM Orchestration Frameworks:**
- **[LangChain](https://qdrant.tech/documentation/frameworks/langchain/)** -- First-class integration as a `QdrantVectorStore`. Supports dense, sparse, and hybrid retrieval. Distributed as a LangChain partner package (`langchain-qdrant`). The most popular integration by usage.
- **[LlamaIndex](https://qdrant.tech/documentation/frameworks/llama-index/)** -- `QdrantVectorStore` for LlamaIndex's data framework. Supports document ingestion, indexing, and query pipelines backed by Qdrant.
- **[Haystack](https://qdrant.tech/documentation/frameworks/)** -- Integration with deepset's Haystack NLP framework for building RAG and search pipelines.
- **[AutoGen / CrewAI / Semantic Kernel](https://qdrant.tech/partners/)** -- Integrations for Microsoft's agentic frameworks and multi-agent systems, using Qdrant as persistent memory and knowledge retrieval.

**Embedding Providers:**
- **OpenAI** -- Direct embedding API compatibility. Qdrant's FastEmbed library provides local alternative models.
- **Cohere** -- Embed API support for text and multilingual embeddings.
- **[FastEmbed](https://github.com/qdrant/fastembed)** -- Qdrant's own lightweight, fast embedding library supporting ONNX models for local inference without GPU dependency. Supports text, image, and sparse embeddings.

**Data Pipeline Tools:**
- **[Airbyte](https://airbyte.com/data-engineering-resources/fundamentals-of-qdrant)** -- ELT connector for loading data from 300+ sources into Qdrant.
- **[Unstructured](https://qdrant.tech/documentation/frameworks/)** -- Document parsing and preprocessing pipeline that feeds into Qdrant.
- **[n8n](https://qdrant.tech/blog/2025-recap/)** -- Official node for the n8n workflow automation platform.

**Monitoring and Observability:**
- **Prometheus** -- Native metrics endpoint at `/metrics` for Prometheus scraping.
- **Grafana** -- Community dashboards available for visualizing Qdrant metrics.
- **OpenTelemetry** -- Request tracing support for distributed tracing systems.

### Common Integration Patterns

**RAG Pipeline: LangChain + Qdrant + OpenAI**

The most common integration pattern. Documents are chunked, embedded via OpenAI's API, stored in Qdrant with metadata payloads, and retrieved at query time to augment LLM prompts:

```
Documents → Chunker → OpenAI Embeddings → Qdrant (store)
User Query → OpenAI Embedding → Qdrant (search) → Top-K chunks → LLM (generate answer)
```

This pattern works with any embedding provider (Cohere, FastEmbed, HuggingFace models) and any LLM (Claude, GPT, Llama, Mistral).

**Agentic RAG: AI Agents + Qdrant as Memory**

In agentic AI architectures, Qdrant serves as both long-term memory and knowledge retrieval. Agents (built with LangChain, AutoGen, or CrewAI) store conversation history, retrieved facts, and intermediate reasoning steps as vectors. On each turn, the agent retrieves relevant context from Qdrant to inform its next action. Qdrant's filtering enables agents to scope retrieval by conversation session, user, topic, or time window.

**Hybrid Search Pipeline: Dense + Sparse + Reranking**

For applications requiring both semantic and keyword precision, combine Qdrant's dense and sparse vector support:

```
Query → Dense Embedding (semantic meaning)
      → Sparse Embedding (keyword terms, e.g., SPLADE/BM25)
      → Qdrant Hybrid Search (RRF fusion of dense + sparse results)
      → Optional: Cross-encoder reranker for final precision
```

This pattern is especially effective for e-commerce search, legal document retrieval, and technical documentation where both meaning and specific terminology matter.

**Real-Time Feature Store: Embedding Lookup for ML**

Use Qdrant as a real-time feature store for ML models that need nearest-neighbor features. Store user/item embeddings and retrieve similar users or items at inference time to feed collaborative filtering or ranking models. Qdrant's gRPC API and low-latency search make it suitable for online serving with p99 latency requirements under 50ms.
