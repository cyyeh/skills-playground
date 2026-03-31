## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [NVIDIA NeMo Agent Toolkit](https://developer.nvidia.com/nemo-agent-toolkit) | official-docs
- [NVIDIA NeMo](https://www.nvidia.com/en-us/ai-data-science/products/nemo/) | official-docs
- [NVIDIA NIM](https://docs.nvidia.com/nim/large-language-models/latest/function-calling.html) | official-docs
- [NVIDIA Nemotron](https://www.nvidia.com/en-us/ai-data-science/foundation-models/nemotron/) | official-docs
- [OpenClaw MCP Integration](https://dev.to/ollieb89/how-openclaw-implements-mcp-for-multi-agent-orchestration-36hk) | article
-->

NemoClaw sits at the intersection of NVIDIA's AI infrastructure stack and the broader open-source agent ecosystem. Understanding its position in this ecosystem helps clarify what NemoClaw does and doesn't do, and how it connects to other tools you might use.

### NVIDIA's AI Stack

**NVIDIA NeMo Framework**
NeMo is NVIDIA's end-to-end platform for building, customizing, and deploying generative AI models. It covers the full model lifecycle: data curation, pretraining, fine-tuning, alignment (RLHF/DPO), and evaluation. NemoClaw uses models produced by the NeMo framework (particularly the Nemotron family) but does not itself train or fine-tune models. The relationship: NeMo produces the models, NemoClaw provides the secure runtime to use them.

**NVIDIA Nemotron Models**
The Nemotron family is NVIDIA's open-source LLM lineup optimized for enterprise tasks: instruction following, agentic reasoning, and tool use. Key models include:
- **Nemotron 3 Nano 4B** — Lightweight model for edge and local deployment
- **Nemotron 3 Super 120B (A12B)** — Mixture-of-experts model with 120B total parameters but only 12B active per token, providing strong reasoning at efficient compute cost
- NemoClaw defaults to `nvidia/nemotron-3-super-120b-a12b` via NVIDIA Endpoints, but supports any model via Ollama or custom providers.

**NVIDIA NIM (Inference Microservices)**
NIM provides containerized, optimized inference endpoints for NVIDIA models. NemoClaw can route inference requests to NIM-hosted models via the NVIDIA Endpoints provider. NIM handles the GPU optimization (TensorRT-LLM acceleration, batching, quantization); NemoClaw handles the security and policy layer around inference routing.

**NVIDIA TensorRT-LLM**
TensorRT-LLM is NVIDIA's high-performance inference engine that optimizes transformer models for NVIDIA GPUs. When NemoClaw routes inference to local Nemotron models, TensorRT-LLM provides the actual inference acceleration — handling kernel fusion, in-flight batching, and quantization. NemoClaw does not directly invoke TensorRT-LLM; it connects through NIM or Ollama, which use TensorRT-LLM under the hood.

**NVIDIA NeMo Agent Toolkit (AgentIQ)**
The NeMo Agent Toolkit (formerly AgentIQ) is a framework-agnostic library for connecting, evaluating, and accelerating teams of AI agents. It provides:
- Unified monitoring and observability across agent frameworks
- Agent Performance Primitives (APP) for parallel execution and speculative branching
- MCP client support for connecting to external tool servers
- Integration with LangChain, LlamaIndex, CrewAI, and custom frameworks

NemoClaw and the Agent Toolkit are complementary: the Agent Toolkit optimizes agent performance and observability, while NemoClaw provides the secure runtime. NemoClaw installs the OpenShell runtime, which is part of the Agent Toolkit.

**NVIDIA NeMo Guardrails**
NeMo Guardrails is a toolkit for adding programmable behavioral constraints to LLM applications. It enables:
- Topical guardrails (keep the agent on-topic)
- Safety guardrails (prevent harmful outputs)
- Security guardrails (block prompt injection attempts)
- Output format enforcement

NemoClaw integrates with Guardrails to apply behavioral constraints at the application level, complementing its kernel-level security. Guardrails handles *what the agent says*; NemoClaw handles *what the agent can do*.

### OpenClaw Ecosystem

**OpenClaw (The Agent Framework)**
OpenClaw is the foundation that NemoClaw secures. It is an open-source AI assistant framework supporting:
- Multi-channel deployment (Telegram, Discord, Slack, WhatsApp, terminal)
- Plugin architecture for extending agent capabilities
- MCP (Model Context Protocol) integration for standardized tool access
- Persistent operation as an always-on service
- Multi-agent orchestration with supervisor-worker patterns

**OpenClaw Plugin System**
OpenClaw's plugin architecture provides two extension mechanisms:
- **Agent Tools:** Functions the LLM can call, registered via `api.registerTool()` with typed schemas
- **Lifecycle Plugins:** Background services that hook into the agent's lifecycle for authentication, logging, and workflow modification

NemoClaw itself runs as an OpenClaw plugin, injecting security controls into the agent's lifecycle without modifying OpenClaw's core codebase.

**MCP (Model Context Protocol) Integration**
OpenClaw natively supports MCP, Anthropic's open standard for connecting LLMs to external tools and data sources. MCP integration happens at three levels:
1. **Server-level:** OpenClaw can host MCP servers, exposing its tools to other MCP-compatible clients
2. **Client-level:** OpenClaw can connect to external MCP servers to access their tools
3. **Gateway-level:** The Composio plugin provides managed OAuth and authentication for hundreds of SaaS integrations via MCP

NemoClaw governs MCP connections through its network policy — MCP servers that require network access are subject to the same deny-by-default rules as any other outbound connection.

### Third-Party Integrations

**Messaging Platforms**
NemoClaw agents communicate through bridges that relay messages via SSH, avoiding direct network sockets:
- Telegram — via bot API bridge
- Discord — via bot bridge
- Slack — via app bridge
- WhatsApp — via gateway bridge

**SaaS Connectors (via Composio)**
The Composio plugin provides pre-built MCP connectors for enterprise services:
- Salesforce, HubSpot (CRM)
- Jira, Linear (Project management)
- GitHub, GitLab (Code repositories)
- Google Workspace, Microsoft 365 (Productivity)
- Datadog, PagerDuty (DevOps)

**Container Runtimes**
NemoClaw supports multiple container runtimes:
- Docker on Linux (primary)
- Colima or Docker Desktop on macOS
- Docker Desktop with WSL on Windows

### Hardware Platforms

NemoClaw runs on a range of NVIDIA hardware:
- **NVIDIA GeForce RTX** PCs and laptops (consumer-grade local inference)
- **NVIDIA RTX PRO** workstations (professional workloads)
- **NVIDIA DGX Station** and **DGX Spark** (enterprise-grade local deployment)
- **Cloud GPU instances** (any provider with NVIDIA GPU access)
- **CPU-only environments** (when using cloud inference routing)

The minimum hardware requirement is modest (4 vCPU, 8 GB RAM) because NemoClaw itself does not run models — it orchestrates access to models running elsewhere. GPU requirements arise only when running local Nemotron models.

### Ecosystem Comparison

| Capability | NemoClaw | LangChain | OpenAI Assistants | Anthropic MCP |
|---|---|---|---|---|
| Agent runtime | Yes (OpenClaw) | Build-your-own | API-hosted | Client library |
| Kernel-level sandboxing | Yes (OpenShell) | No | Managed by OpenAI | No |
| Privacy routing | Yes (local/cloud) | Manual | Cloud-only | Cloud-only |
| Tool calling | Yes (typed schemas) | Yes (tool classes) | Yes (JSON schema) | Yes (JSON schema) |
| Network policy | Deny-by-default YAML | No | N/A (cloud) | No |
| MCP support | Yes (via OpenClaw) | Via adapter | No | Native |
| Always-on operation | Yes | With custom infra | No | No |
| Audit logging | Kernel-level | Application-level | Via API logs | No |
| Open source | Yes (Apache 2.0) | Yes (MIT) | No | Protocol is open |
