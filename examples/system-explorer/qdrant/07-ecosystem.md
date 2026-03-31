## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [LangChain Integration](https://qdrant.tech/documentation/frameworks/langchain/) | docs
- [LlamaIndex Integration](https://qdrant.tech/documentation/frameworks/llama-index/) | docs
- [Qdrant Cloud](https://qdrant.tech/cloud/) | official
- [Qdrant Hybrid Cloud](https://qdrant.tech/hybrid-cloud/) | official
- [Qdrant Pricing](https://qdrant.tech/pricing/) | official
-->

### Framework Integrations

Qdrant has first-class integrations with the major AI/ML frameworks:

#### LangChain
LangChain is the most widely used LLM application framework. Qdrant integrates as a vector store via the `langchain-qdrant` package, supporting:
- Dense and sparse vector search
- Hybrid retrieval combining semantic and lexical search
- Metadata filtering using LangChain's filter syntax
- Async operations for high-throughput pipelines
- Multi-tenancy via collection partitioning

```python
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings

vectorstore = QdrantVectorStore.from_documents(
    documents,
    OpenAIEmbeddings(),
    url="http://localhost:6333",
    collection_name="my_docs",
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
```

#### LlamaIndex
LlamaIndex simplifies data ingestion and indexing for LLM applications. Qdrant serves as a vector store backend:
- Supports all Qdrant vector types (dense, sparse, multivector)
- Hybrid search with fusion strategies
- Multi-tenancy with user-level filtering
- Batch ingestion optimizations

```python
from llama_index.vector_stores.qdrant import QdrantVectorStore

vector_store = QdrantVectorStore(
    client=qdrant_client,
    collection_name="my_index",
    enable_hybrid=True,
)
```

#### Haystack
Deepset's Haystack framework uses Qdrant as a document store for building search and RAG pipelines. The `QdrantDocumentStore` supports embedding retrieval, filtering, and batch operations.

#### Microsoft Semantic Kernel
Qdrant integrates with Microsoft's Semantic Kernel as a memory store, enabling AI agents to persist and retrieve semantic memories across conversation sessions.

#### Spring AI
For Java/Spring Boot applications, Qdrant provides a vector store integration through Spring AI, enabling enterprise Java applications to leverage vector search.

### Embedding Model Integrations

Qdrant works with any embedding model that produces fixed-length vectors. Common pairings include:

| Provider | Models | Dimensions |
|----------|--------|------------|
| OpenAI | text-embedding-3-small/large | 1536 / 3072 |
| Cohere | embed-v3 | 1024 |
| Google | text-embedding-004 | 768 |
| Voyage AI | voyage-3 | 1024 |
| HuggingFace | BGE, GTE, E5, all-MiniLM | 384-1024 |
| Jina AI | jina-embeddings-v3 | 1024 |
| Ollama | nomic-embed-text, mxbai-embed | 768-1024 |

For sparse vectors, common models include SPLADE++, BM25 (via Qdrant's built-in tokenizer), and miniCOIL.

### Qdrant Cloud

Qdrant offers three managed deployment options:

#### Managed Cloud
- Fully managed clusters on AWS, GCP, or Azure
- Free 1GB tier (no credit card required)
- Automatic backups, monitoring, and alerting
- Zero-downtime upgrades for HA clusters
- Pay-as-you-go billing based on compute, memory, storage, and inference tokens

#### Hybrid Cloud
- Managed Qdrant clusters running in your own Kubernetes infrastructure
- Data stays within your network — Qdrant Cloud only manages the control plane
- Supports any cloud provider, on-premises, or edge environments
- Starting at $0.014/hour

#### Private Cloud
- Full control over Qdrant database clusters in any Kubernetes environment
- Custom pricing for enterprise deployments
- Suitable for organizations with strict data sovereignty requirements

### Qdrant Edge

Introduced in v1.17, **Qdrant Edge** is an in-process version of Qdrant that shares the same internals, storage format, and Points API as the server version. It enables:
- Embedding Qdrant directly in applications without a separate server process
- Edge computing deployments with limited resources
- Mobile and IoT applications requiring local vector search
- Testing and development without running a server

### Observability & DevOps

- **Prometheus metrics** — Exposed at `/metrics` endpoint for Grafana dashboards
- **OpenTelemetry** — Distributed tracing support for debugging search pipelines
- **Qdrant Web Dashboard** — Built-in UI for browsing collections, points, and running test queries
- **Helm Charts** — Official Kubernetes deployment charts with configurable replicas, resources, and persistence
- **Terraform** — Community providers for infrastructure-as-code deployments

### Data Migration Tools

- **Qdrant Migration Tool** — CLI tool for migrating between Qdrant instances
- **Snapshot API** — Create and restore collection snapshots for backup and migration
- **Bulk Upload APIs** — Streaming upload endpoints optimized for large-scale data ingestion
