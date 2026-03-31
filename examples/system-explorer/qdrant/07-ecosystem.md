## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [Qdrant Integrations Documentation](https://qdrant.tech/documentation/frameworks/) | official-docs
- [Qdrant Client Libraries](https://qdrant.tech/documentation/interfaces/) | official-docs
- [Qdrant Cloud](https://cloud.qdrant.io/) | official-docs
- [LangChain Qdrant Integration](https://qdrant.tech/documentation/frameworks/langchain/) | official-docs
-->

### Official Client Libraries

**Python (`qdrant-client`):** The most feature-complete client. Supports sync and async operations, local mode (in-memory, no server needed), automatic batching, and full type hints. Local mode uses the same Rust engine compiled to a Python extension, providing identical behavior for development and testing without running a server.

```python
from qdrant_client import QdrantClient

# Local mode — no server needed
client = QdrantClient(":memory:")  # in-memory
client = QdrantClient(path="./local_db")  # persistent local

# Remote server
client = QdrantClient(url="http://localhost:6333")
client = QdrantClient(url="https://cloud.qdrant.io", api_key="...")
```

**JavaScript/TypeScript (`@qdrant/js-client-rest`):** REST-based client for Node.js and browser environments. Supports all CRUD and search operations with TypeScript type definitions.

**Rust (`qdrant-client`):** Native Rust client using gRPC for maximum performance. Ideal for Rust applications that need minimal latency.

**Go (`go-client`):** gRPC-based client for Go applications.

**.NET (`Qdrant.Client`):** Official C# client for .NET applications, supporting both REST and gRPC.

**Java (`java-client`):** gRPC-based client for Java/Kotlin applications.

**Raw API Access:** Any language with HTTP or gRPC support can use Qdrant directly. The REST API is available on port 6333 and the gRPC API on port 6334.

### Framework Integrations

**LangChain:** Qdrant is a first-class vector store in the LangChain ecosystem, available as the `langchain-qdrant` partner package. It supports dense, sparse, and hybrid retrieval out of the box. Qdrant acts as the retrieval backend for LangChain's RAG chains, agent memory, and document loaders.

```python
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings

vectorstore = QdrantVectorStore.from_documents(
    documents,
    embedding=OpenAIEmbeddings(),
    url="http://localhost:6333",
    collection_name="langchain_docs",
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
```

**LlamaIndex:** Qdrant integrates as a vector store backend for LlamaIndex, handling the chunking-embedding-storage pipeline. LlamaIndex manages document ingestion and query orchestration while Qdrant provides the similarity search layer.

**Haystack:** Deepset's Haystack framework includes a `QdrantDocumentStore` for building search and question-answering pipelines. Supports hybrid retrieval with both dense and sparse representations.

**Semantic Kernel (Microsoft):** Qdrant serves as a memory backend for Microsoft's Semantic Kernel, enabling AI applications built with .NET or Python to persist and retrieve contextual information.

**AutoGen / CrewAI / Other Agent Frameworks:** Qdrant is commonly used as the long-term memory store for multi-agent systems, providing agents with the ability to recall relevant past interactions and knowledge.

### Embedding Model Compatibility

Qdrant is embedding-model agnostic -- it works with any model that produces numerical vectors:

- **OpenAI:** `text-embedding-3-small` (1536d), `text-embedding-3-large` (3072d, supports Matryoshka dimensions)
- **Cohere:** `embed-v3` (1024d), works well with binary quantization
- **Sentence-Transformers:** `all-MiniLM-L6-v2` (384d), `all-mpnet-base-v2` (768d)
- **Fastembed (Qdrant's own):** Lightweight embedding library that runs models locally without external API calls. Integrated directly into `qdrant-client` for zero-configuration embedding.
- **CLIP / SigLIP:** Multimodal embeddings for image-text search
- **BGE / GTE / E5:** Open-source embedding models from various providers
- **Qwen3 Embeddings:** Latest Chinese/multilingual embedding models

**Qdrant Cloud Inference:** A managed service that unifies embedding generation and vector search into a single API call. You send raw text, and Qdrant Cloud handles embedding and search in one round trip, reducing latency and simplifying the client-side code.

### Deployment Options

**Open Source (Self-Hosted):** Run the Qdrant Docker image or compile from source. Full feature set, unlimited scale, no license fees. You manage infrastructure, backups, and upgrades.

**Qdrant Cloud (Managed):** Fully managed clusters on AWS, GCP, or Azure. Includes automatic scaling, backups, monitoring, and a free tier (1GB storage). Production deployments get SLA guarantees, SSO, and role-based access control.

**Hybrid Cloud:** Run Qdrant in your own infrastructure (on-premises or private cloud) with management plane in Qdrant Cloud. Combines data sovereignty with managed operations.

**Qdrant Edge:** An in-process version of Qdrant (sharing the same storage format as the server) for edge/mobile deployments. Enables low-latency, offline-capable vector search directly on devices.

### Common Integration Patterns

**Qdrant + LangChain/LlamaIndex for RAG:** The most common pattern. Documents are chunked, embedded, and stored in Qdrant. At query time, LangChain/LlamaIndex embeds the user question, retrieves relevant chunks from Qdrant, and passes them to the LLM as context. Qdrant's payload filtering enables scoping retrieval by document source, date, or access level.

**Qdrant + Fastembed for Self-Contained Search:** Use Fastembed (Qdrant's lightweight embedding library) to generate embeddings locally without external API calls. This pattern is ideal for privacy-sensitive applications or offline deployments where you can't call OpenAI/Cohere APIs.

**Qdrant + Kafka/RabbitMQ for Streaming Ingestion:** For high-throughput ingestion, use a message queue to buffer incoming data. A consumer service reads from the queue, embeds the data, and batch-upserts into Qdrant. This decouples ingestion rate from Qdrant's indexing speed and provides backpressure handling.

**Qdrant + PostgreSQL for Hybrid Storage:** Store structured data (user profiles, transactions, relationships) in PostgreSQL and vector embeddings in Qdrant. Application logic queries both systems: PostgreSQL for relational queries, Qdrant for similarity search. Join results in the application layer.

**Qdrant + Prometheus/Grafana for Monitoring:** Qdrant exposes Prometheus metrics at the `/metrics` endpoint. Set up Grafana dashboards to monitor search latency, ingestion throughput, segment counts, memory usage, and optimizer activity. Alert on degraded performance (rising latency, growing segment count).
