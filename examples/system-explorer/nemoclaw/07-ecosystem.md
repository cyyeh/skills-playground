## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [NVIDIA Agent Toolkit](https://developer.nvidia.com/agent-toolkit) | official-docs
- [NemoClaw GitHub](https://github.com/NVIDIA/NemoClaw) | github
- [OpenShell Technical Blog](https://developer.nvidia.com/blog/run-autonomous-self-evolving-agents-more-safely-with-nvidia-openshell/) | blog
- [NeMo Guardrails GitHub](https://github.com/NVIDIA-NeMo/Guardrails) | github
-->

### NVIDIA Ecosystem

**OpenClaw:** The autonomous AI assistant that NemoClaw secures. OpenClaw provides the agentic capabilities (code generation, task planning, tool use), and NemoClaw provides the security envelope. NemoClaw is purpose-built for OpenClaw's architecture and lifecycle.

**OpenShell:** The general-purpose agent security runtime underneath NemoClaw. OpenShell provides sandboxing, policy enforcement, and the privacy router as reusable primitives. While NemoClaw configures OpenShell specifically for OpenClaw, OpenShell also works with other agents like Claude Code, Cursor, and Codex. If you use a different agent, you'd use OpenShell directly.

**NVIDIA Agent Toolkit:** The broader software suite that includes OpenShell, inference management tools, and deployment utilities. NemoClaw is one application built on Agent Toolkit components.

**NVIDIA Nemotron:** The family of open-source language models from NVIDIA. NemoClaw's default inference configuration uses `nvidia/nemotron-3-super-120b-a12b`, a 120-billion-parameter model optimized for agent tasks. Nemotron models can run locally on NVIDIA GPUs for privacy-sensitive inference.

**NeMo Guardrails:** A separate but related NVIDIA project that provides programmable guardrails for LLM-based conversational systems. NeMo Guardrails operates at the prompt/response level (controlling what the LLM says), while NemoClaw operates at the infrastructure level (controlling what the agent can do). They address different threat models and can be used together.

**NVIDIA Endpoints (NIM):** Cloud-hosted inference endpoints for running NVIDIA models. NemoClaw integrates with NVIDIA Endpoints as a default inference provider, routing requests through the privacy router based on configured policies.

### Inference Providers

NemoClaw supports routing inference to multiple providers, each with different trade-offs:

| Provider | Type | Privacy | Capability | Cost | Status |
|----------|------|---------|-----------|------|--------|
| NVIDIA Endpoints | Cloud | Moderate | High (Nemotron) | Pay-per-use | Supported |
| OpenAI | Cloud | Low | High (GPT-4+) | Pay-per-use | Supported |
| Anthropic | Cloud | Low | High (Claude) | Pay-per-use | Supported |
| Google Gemini | Cloud | Low | High (Gemini) | Pay-per-use | Supported |
| Ollama (local) | Local | High | Variable | Hardware only | Experimental |
| vLLM (local) | Local | High | Variable | Hardware only | Experimental |

### Messaging Integrations

NemoClaw's host-side messaging bridges connect the sandboxed agent to external communication platforms:

**Telegram:** Configure via `TELEGRAM_BOT_TOKEN` environment variable. The bridge runs as a host process, forwarding messages to/from the sandbox.

**Discord:** Configure via `DISCORD_BOT_TOKEN` environment variable. Supports server channels and direct messages.

**Slack:** Configure via Slack app credentials. Integrates with workspace channels and direct messages.

All bridges run on the host, not inside the sandbox. This ensures messaging platform credentials are never exposed to the agent.

### Container Runtimes

| Runtime | Platform | Support Level |
|---------|----------|--------------|
| Docker | Linux | Primary |
| Colima | macOS (Apple Silicon) | Supported |
| Docker Desktop | macOS, Windows WSL | Supported |
| Podman | Linux | Supported |
| Podman (macOS Intel) | macOS (Intel) | Not yet supported |

### Kubernetes Support

The `k8s/` directory in the repository contains Kubernetes manifests for deploying NemoClaw in cluster environments. This enables running sandboxed agents as Kubernetes pods with the same security policies applied at the container level.

### Complementary Tools

**NeMo Guardrails:** For prompt-level guardrails (topic steering, output filtering, dialog management) alongside NemoClaw's infrastructure-level security.

**NVIDIA NIM:** For hosting and serving NVIDIA models locally or in a private cloud, providing the local inference endpoint that NemoClaw's privacy router can target.

**Standard Monitoring Stack:** NemoClaw's sandbox produces logs accessible via `nemoclaw <name> logs`. These can be forwarded to standard monitoring tools (Grafana, Prometheus, ELK) for operational visibility.

### Community and Support

- **GitHub:** [NVIDIA/NemoClaw](https://github.com/NVIDIA/NemoClaw) -- 18,000+ stars, 2,100+ forks
- **Discord:** NVIDIA developer community channel
- **GitHub Discussions:** For questions and feature requests
- **GitHub Issues:** For bug reports
- **Security Reporting:** NVIDIA Vulnerability Disclosure Program, `psirt@nvidia.com`, or GitHub private security advisories
