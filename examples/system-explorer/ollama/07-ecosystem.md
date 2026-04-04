## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [Ollama GitHub Repository](https://github.com/ollama/ollama) | github
- [Ollama Model Library](https://ollama.com/library) | official-docs
- [Ollama Documentation](https://docs.ollama.com/) | official-docs
-->

### Official Tools & Extensions

**Ollama CLI** -- The primary interface for model management. Commands like `ollama run`, `ollama pull`, `ollama create`, and `ollama ps` handle the full model lifecycle. The CLI includes an interactive TUI mode that launches when called without arguments.

**Ollama Model Library** -- The official registry at [ollama.com/library](https://ollama.com/library) hosts hundreds of pre-built models with various quantization levels. Models from Meta (Llama), Google (Gemma), Alibaba (Qwen), Mistral, Microsoft (Phi), and community fine-tunes are all available. Users can also push custom models to their own namespaces.

**OpenAI-Compatible API** -- Built-in `/v1/chat/completions`, `/v1/completions`, and `/v1/embeddings` endpoints that implement the OpenAI API specification. Any application using the OpenAI SDK can point to Ollama by changing the base URL, with no other code changes required.

**Web Search and Web Fetch** -- As of recent versions, Ollama includes built-in web search and fetch capabilities through the OpenClaw plugin system, allowing models to access real-time web content during conversations.

### Community Ecosystem

**Client Libraries:**
- [ollama-python](https://github.com/ollama/ollama-python) -- Official Python client library
- [ollama-js](https://github.com/ollama/ollama-js) -- Official JavaScript/TypeScript client
- Community clients exist for Go, Rust, Ruby, Java, C#, Swift, and Dart

**AI Coding Tools:**
- **Continue** -- Open-source AI code assistant that uses Ollama for local code completion and chat
- **Cline** -- Autonomous coding agent in VS Code with Ollama backend support
- **Cursor/Windsurf** -- IDE integrations that can use Ollama for local model access
- **Aider** -- AI pair programming tool that supports Ollama models

**RAG and Agent Frameworks:**
- **LangChain** -- Full integration with Ollama as an LLM provider via `ChatOllama`
- **LlamaIndex** -- Supports Ollama for both LLM inference and embedding generation
- **CrewAI** -- Multi-agent framework with Ollama backend support
- **Haystack** -- NLP pipeline framework with Ollama integration
- **Open WebUI** -- Full-featured web interface for Ollama with conversation management, RAG, and multi-user support

**Desktop Applications:**
- **Open WebUI** -- The most popular web frontend for Ollama, providing a ChatGPT-like experience
- **Jan** -- Desktop AI assistant with Ollama-compatible model support
- **Msty** -- macOS-native chat interface for Ollama

### Common Integration Patterns

**Ollama + Open WebUI for team chat.** Deploy Ollama as a backend server and Open WebUI as the frontend for a self-hosted ChatGPT alternative. Open WebUI adds user accounts, conversation history, RAG document upload, and a polished UI. This pattern is popular for teams that want to share local LLM access without everyone running models on their own machines.

**Ollama + LangChain/LlamaIndex for RAG.** Use Ollama's embedding endpoint (`nomic-embed-text` or `mxbai-embed-large`) to vectorize documents, store in a vector database (Chroma, Qdrant, Weaviate), and use Ollama's chat endpoint for generation. The entire pipeline runs locally with no external API calls.

**Ollama + VS Code extensions for coding.** Configure Continue or Cline to use Ollama as the local model backend. Code completion, refactoring suggestions, and code explanations all run on your machine. This is popular among developers working on proprietary codebases who cannot send code to cloud APIs.

**Ollama as a development proxy.** Use Ollama in development and CI/CD pipelines as a stand-in for production LLM APIs. The OpenAI-compatible endpoint means your test suites and development environments can use local models, switching to production APIs (OpenAI, Anthropic) via environment variable changes.
