## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [NVIDIA Agent Toolkit](https://docs.nvidia.com/nemoclaw/latest/about/overview.html) | official-docs
- [NemoClaw Inference Profiles](https://docs.nvidia.com/nemoclaw/latest/reference/inference-profiles.html) | official-docs
- [awesome-nemoclaw](https://github.com/VoltAgent/awesome-nemoclaw) | github
-->

### Official Tools & Extensions

**NVIDIA OpenShell** -- The runtime foundation that NemoClaw builds on. OpenShell provides kernel-level sandboxing, network namespace isolation, and the gateway that routes inference requests. While NemoClaw can be thought of as a purpose-built configuration for OpenShell, OpenShell itself is a general-purpose agent runtime that can host other agent frameworks beyond OpenClaw -- like how Docker can run any containerized application, not just the one you happen to use most.

**NVIDIA Nemotron** -- NVIDIA's family of open-source language models, optimized for the NemoClaw inference pipeline. Nemotron models (including Nemotron 3 Super 120B) can run locally via NVIDIA NIM or accessed through [build.nvidia.com](https://build.nvidia.com/nemoclaw). Using Nemotron with NemoClaw provides the tightest integration because the inference routing is pre-configured for NVIDIA's model endpoints.

**NVIDIA NIM (NVIDIA Inference Microservices)** -- A containerized inference runtime for self-hosting LLMs on NVIDIA hardware. NemoClaw supports NIM as a local inference backend, allowing the entire agent stack (sandbox + model) to run on-premises with no external API calls -- like having both the factory and the power plant on the same site.

**NVIDIA Agent Toolkit** -- The broader suite that includes OpenShell, NemoClaw, and other tools for building and deploying AI agents. NemoClaw is the Toolkit's answer to the specific problem of running coding assistants securely.

### Community Ecosystem

**awesome-nemoclaw** -- A community-curated collection of [presets, recipes, and playbooks](https://github.com/VoltAgent/awesome-nemoclaw) for sandboxed OpenClaw operations. This repository aggregates community-contributed network policy configurations, deployment scripts, and operational runbooks for common NemoClaw use cases.

**OpenClaw Extensions (ClawHub)** -- NemoClaw's network policy includes an allowlist entry for ClawHub, the OpenClaw extension registry. This means sandboxed agents can install and use OpenClaw extensions (MCP servers, custom tools) within the security boundary. The extension ecosystem that exists for OpenClaw carries directly into NemoClaw deployments.

**Messaging Bridge Community** -- While NemoClaw ships with official bridges for Telegram, Discord, and Slack, the bridge architecture is straightforward enough that community members can build connectors for additional platforms. Each bridge is a standalone script that translates platform-specific messaging APIs into OpenClaw agent messages.

### Common Integration Patterns

**NemoClaw + Ollama for fully local inference.** This is the privacy-maximizing configuration: the agent runs in a sandbox, and all model calls go to a locally-running Ollama instance. No data leaves the machine. NemoClaw handles Ollama setup during onboarding, including model pulling and warming. This pattern suits organizations with strict data sovereignty requirements -- like a self-contained research station that generates its own power and grows its own food.

**NemoClaw + NVIDIA Endpoints for cloud-scale inference.** For teams that need access to larger models (like Nemotron 3 Super 120B) without the hardware to run them locally, NemoClaw routes inference through build.nvidia.com. The sandbox still provides network and filesystem isolation, while the cloud provides model capabilities. The trade-off is that inference data leaves the local machine, though it is encrypted in transit.

**NemoClaw + Telegram/Slack for team-accessible agents.** Connecting a messaging bridge transforms a sandboxed coding agent into a team resource. Multiple team members can interact with the same agent through their existing chat tools. The sandbox ensures that even if a team member asks the agent to do something unexpected, the network policy and approval workflow provide guardrails.

**NemoClaw + GitHub for repository-aware agents.** The default network policy allows access to GitHub's API and hosting endpoints. This enables common workflows where the agent reads repository contents, reviews pull requests, or creates issues -- all within the sandbox. Access to GitHub is read-write at the API level but still subject to the agent's GitHub credentials and the repository's own access controls.

**NemoClaw + custom OpenAI-compatible proxies for enterprise model routing.** Organizations that run model gateways (LiteLLM, vLLM behind a reverse proxy, or custom routing infrastructure) can configure NemoClaw to point at their internal endpoint. NemoClaw validates the endpoint during onboarding by sending a real inference request, since custom proxies often lack standardized `/models` endpoints.
