## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [NVIDIA NemoClaw Developer Guide](https://docs.nvidia.com/nemoclaw/latest/index.html) | official-docs
- [NemoClaw Inference Profiles](https://docs.nvidia.com/nemoclaw/latest/reference/inference-profiles.html) | official-docs
- [Architecting the Agentic Future: OpenClaw vs. NanoClaw vs. NemoClaw](https://dev.to/mechcloud_academy/architecting-the-agentic-future-openclaw-vs-nanoclaw-vs-nvidias-nemoclaw-9f8) | blog
-->

NemoClaw sits at the intersection of the NVIDIA AI platform, the OpenClaw agent ecosystem, and the broader landscape of AI safety and security tooling. Understanding its ecosystem helps you choose the right components and plan integrations.

### Core Dependencies

**OpenClaw**
NemoClaw is built to wrap OpenClaw, the open-source autonomous AI agent framework. OpenClaw provides the agent runtime — task execution, tool use, memory, scheduled jobs, and messaging integrations. NemoClaw does not replace OpenClaw; it adds a security layer on top. Your existing OpenClaw skills, configurations, and workflows carry over into the NemoClaw sandbox.

**NVIDIA OpenShell**
OpenShell is NVIDIA's sandbox runtime for AI agents, part of the NVIDIA Agent Toolkit. It provides the kernel-level isolation primitives (Landlock, seccomp, network namespaces), the inference routing gateway, and the policy enforcement engine. OpenShell is the foundation that NemoClaw's blueprints build upon. OpenShell can be used independently for other agent frameworks, but NemoClaw provides the OpenClaw-specific integration.

**NVIDIA Nemotron Models**
NemoClaw is optimized (but not limited to) NVIDIA's Nemotron model family for local inference. Nemotron models range from the 4B-parameter Nano variant (suitable for edge deployment) to the 120B-parameter Super variant (full local inference with strong capabilities). Using Nemotron models locally keeps all data on-premises, but you can also use OpenAI, Anthropic, Gemini, or any OpenAI-compatible endpoint.

### Inference Provider Ecosystem

NemoClaw supports a broad range of inference providers through the OpenShell gateway:

| Provider | Protocol | Local/Cloud | Notes |
|----------|----------|-------------|-------|
| NVIDIA Endpoints | OpenAI-compatible | Cloud | Hosted on `integrate.api.nvidia.com` |
| OpenAI | Native OpenAI | Cloud | GPT-4o, o3, etc. |
| Anthropic | anthropic-messages | Cloud | Claude 4 Opus, Sonnet, etc. |
| Google Gemini | OpenAI-compatible | Cloud | Via Google's compatible endpoint |
| Ollama | OpenAI-compatible | Local | Any model available in Ollama |
| NVIDIA NIM | OpenAI-compatible | Local | GPU-dependent, experimental |
| vLLM | OpenAI-compatible | Local | Experimental (`localhost:8000`) |
| Custom endpoints | OpenAI or Anthropic | Either | Proxies, gateways, internal APIs |

### Messaging Platform Integrations

NemoClaw supports connecting sandboxed agents to messaging platforms through host-side bridge processes:

- **Telegram** — Bot integration via host-side relay process
- **Discord** — Bot integration via host-side relay process
- **Slack** — App integration via host-side relay process

Messaging bridges run outside the sandbox, maintaining the security boundary. The agent communicates with the bridge through the sandbox's internal API, and messaging credentials never enter the sandbox.

### Complementary Tools

**NanoClaw**
NanoClaw is an alternative lightweight agent framework that takes a different approach to security — using fully containerized, ephemeral environments with Kubernetes-native orchestration. While NemoClaw wraps an existing OpenClaw setup with security controls, NanoClaw builds security into the agent framework from the ground up. Teams evaluating agent platforms should consider both.

**NVIDIA Agent Toolkit**
The broader NVIDIA Agent Toolkit includes tools beyond OpenShell and NemoClaw, such as model optimization tools, inference servers (TensorRT-LLM, Triton), and evaluation frameworks. NemoClaw integrates naturally with other toolkit components for end-to-end agent deployment.

**MCP (Model Context Protocol)**
The Model Context Protocol provides a standard way for AI agents to interact with external tools and data sources. OpenClaw supports MCP servers, and NemoClaw's network policy engine can be configured to allow connections to specific MCP server endpoints while blocking unauthorized access.

### Community Resources

- **GitHub Repository:** [NVIDIA/NemoClaw](https://github.com/NVIDIA/NemoClaw) — Source code, issues, discussions
- **Official Documentation:** [docs.nvidia.com/nemoclaw](https://docs.nvidia.com/nemoclaw/latest/) — Developer guide, API reference
- **Discord Community:** Active community for support and discussion
- **awesome-nemoclaw:** Community-curated collection of presets, recipes, and playbooks for common NemoClaw configurations
