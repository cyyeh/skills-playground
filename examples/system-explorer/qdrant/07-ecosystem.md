## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [Qdrant API & SDKs](https://qdrant.tech/documentation/interfaces/) | official-docs
- [Qdrant LangChain Integration](https://qdrant.tech/documentation/frameworks/langchain/) | official-docs
- [Qdrant LlamaIndex Integration](https://qdrant.tech/documentation/frameworks/llama-index/) | official-docs
- [Qdrant Cloud](https://cloud.qdrant.io/) | official-docs
-->

### Official Client Libraries

Qdrant provides official client libraries across six languages, all maintained by the Qdrant team:

| Language | Package | Installation |
|----------|---------|-------------|
| Python | qdrant-client | `pip install qdrant-client[fastembed]` |
| JavaScript/TypeScript | @qdrant/js-client-rest | `npm install @qdrant/js-client-rest` |
| Rust | qdrant-client | `cargo add qdrant-client` |
| Go | go-client | `go get github.com/qdrant/go-client` |
| .NET | Qdrant.Client | `dotnet add package Qdrant.Client` |
| Java | java-client | Available on Maven Central |

The Python client is the most feature-rich, supporting a local mode that runs an embedded Qdrant instance without a separate server — useful for development, testing, and small-scale applications. For languages without an official client, developers can generate clients from Qdrant's OpenAPI specification or protobuf definitions.

### Framework Integrations

**LangChain:** Qdrant is available as a partner package (`langchain-qdrant`) that provides a QdrantVectorStore class compatible with the LangChain vector store interface. It supports dense, sparse, and hybrid retrieval modes. The integration handles document ingestion, similarity search, and MMR (Maximal Marginal Relevance) search natively.

**LlamaIndex:** Qdrant integrates as a vector store backend for LlamaIndex (formerly GPT Index). The `QdrantVectorStore` class plugs into LlamaIndex's indexing and retrieval pipeline, enabling RAG applications with Qdrant as the knowledge store.

**OpenAI:** Qdrant can serve as a memory backend for ChatGPT via the OpenAI retrieval plugin. It also works seamlessly with OpenAI's embedding models (text-embedding-ada-002, text-embedding-3-small, text-embedding-3-large) and is featured in the OpenAI Cookbook.

**Haystack:** Deepset's Haystack framework includes a Qdrant document store integration for building NLP pipelines with retrieval components.

**AutoGen / CrewAI / Semantic Kernel:** Qdrant integrations exist for Microsoft's agentic frameworks, enabling agent memory and tool-use patterns backed by vector search.

### Embedding Model Support

Qdrant works with any embedding model that produces fixed-dimensional vectors. Popular choices include:

- **OpenAI:** text-embedding-3-small (1536d), text-embedding-3-large (3072d)
- **Cohere:** embed-english-v3.0, embed-multilingual-v3.0
- **Sentence-Transformers:** all-MiniLM-L6-v2 (384d), all-mpnet-base-v2 (768d)
- **Hugging Face models:** Any model available on the Hub that produces embeddings
- **FastEmbed:** Qdrant's own lightweight embedding library (included in the Python client via the `[fastembed]` extra) for on-device embedding generation without external API calls

### Qdrant Cloud

Qdrant Cloud is the managed service offering, providing:

- **Managed clusters:** Deploy Qdrant clusters on AWS, GCP, or Azure without managing infrastructure.
- **Auto-scaling:** Clusters scale based on workload demands.
- **Terraform support:** Infrastructure-as-code deployment via the Qdrant Cloud API.
- **SSO and RBAC:** Enterprise authentication and role-based access control (introduced 2025).
- **Granular API keys:** Database-level API keys with configurable permissions.
- **Free tier:** A limited free cluster for development and experimentation.

### Web UI

Qdrant ships with a built-in Web UI (accessible at the REST API port) that provides a visual interface for:
- Browsing collections and their configurations
- Inspecting individual points with their vectors and payloads
- Running test searches and exploring results
- Viewing cluster status and shard distribution
- Managing snapshots

### Deployment Options

- **Docker:** The most common deployment method. `docker run -p 6333:6333 qdrant/qdrant`
- **Binary:** Standalone binary available from GitHub releases for Linux, macOS, and Windows.
- **Kubernetes:** Helm chart available for Kubernetes deployments with distributed mode.
- **Qdrant Cloud:** Fully managed service.
- **Embedded (Python):** The Python client's local mode runs an embedded Qdrant instance in-process, backed by the same Rust engine via PyO3 bindings.
