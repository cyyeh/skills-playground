## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
<!-- references:
- [NemoClaw Overview](https://docs.nvidia.com/nemoclaw/latest/about/overview.html) | official-docs
- [NVIDIA NemoClaw: Engineering Autonomy Within Enterprise Guardrails](https://hyperframeresearch.com/2026/03/24/nvidia-nemoclaw-engineering-autonomy-within-enterprise-guardrails/) | blog
- [Nvidia NemoClaw Brings Security to OpenClaw](https://venturebeat.com/technology/nvidia-lets-its-claws-out-nemoclaw-brings-security-scale-to-the-agent) | blog
-->

### When to Use NemoClaw

**Always-On AI Assistants in Enterprise Environments:** You need an AI agent that runs continuously -- answering questions, writing code, automating tasks -- but your security team requires strict control over what the agent can access. NemoClaw provides the isolation guarantees that make always-on agents acceptable in enterprise environments.

**Privacy-Sensitive Development Work:** Your team works with proprietary code, internal APIs, or customer data. You want the productivity benefits of an AI coding assistant but cannot allow prompts containing sensitive context to leave your network. NemoClaw's privacy router keeps sensitive inference local while allowing cloud models for non-sensitive tasks.

**Multi-Provider Inference Management:** You use different LLM providers for different tasks (e.g., OpenAI for creative writing, Anthropic for safety-critical analysis, local Nemotron for confidential data). NemoClaw's inference routing centralizes provider management and ensures the right provider handles the right requests.

**Sandboxed Code Execution:** Your agent generates and runs code. Without sandboxing, a hallucinated `rm -rf /` or a malicious pip package could damage your system. NemoClaw's filesystem and process isolation contain the blast radius to the sandbox directory.

**Team Agent Deployment:** You manage agents for multiple team members and need a standardized, reproducible deployment. NemoClaw's blueprint system ensures every agent gets the same security baseline, and state migration enables moving agents between machines.

### When NOT to Use NemoClaw

**You Don't Use OpenClaw:** NemoClaw is specifically built for OpenClaw. If you use a different AI agent (Claude Code, Cursor, Windsurf), you would use OpenShell directly rather than NemoClaw, as NemoClaw's blueprint and onboarding are OpenClaw-specific.

**Production Workloads (Today):** NemoClaw is in alpha. APIs, configuration schemas, and runtime behavior are subject to breaking changes between releases. For production deployments, wait for a stable release.

**Simple, Stateless LLM Usage:** If you just need to send prompts to an LLM API and get responses -- no autonomous agent, no code execution, no persistent state -- NemoClaw's overhead is unnecessary. Use the LLM API directly or through a lightweight SDK.

**Windows-Only Environments:** NemoClaw requires Linux (Ubuntu 22.04+) or macOS with Docker. There is no native Windows support; WSL with Docker Desktop is the workaround, but it adds complexity and potential performance overhead.

**Resource-Constrained Machines:** The sandbox image is approximately 2.4 GB compressed, and the system requires a minimum of 8 GB RAM (16 GB recommended). Machines with less than 8 GB RAM may experience out-of-memory issues. If you're working on a lightweight laptop or VPS, NemoClaw may not be practical.

**Multi-Tenant or Multi-Agent Governance:** NemoClaw operates at the single-sandbox level. If you need to manage policies, permissions, and audit trails across multiple teams, agents, and environments, you need an orchestration layer above NemoClaw. The tool does not provide fleet management or cross-tenant governance.

### Real-World Use Cases

**Secure Coding Assistant on DGX Spark:** A development team deploys NemoClaw on an NVIDIA DGX Spark workstation. The agent runs Nemotron locally for all code review and generation tasks involving proprietary source code. For architectural planning and documentation, it routes to a frontier cloud model. The privacy router ensures no proprietary code leaves the local network.

**Research Lab Agent with Controlled Internet Access:** A research lab runs NemoClaw to give an AI agent access to internal datasets and compute resources. The network policy allowlists only specific academic API endpoints (arXiv, Semantic Scholar) and the team's internal registry. The agent can fetch papers and search for relevant work but cannot access social media, arbitrary websites, or exfiltrate data.

**DevOps Automation with Guardrails:** A platform engineering team uses NemoClaw to run an agent that automates infrastructure tasks: writing Terraform configurations, debugging CI failures, and managing Kubernetes manifests. The sandbox filesystem isolation prevents the agent from accessing production credentials stored outside `/sandbox`, and the seccomp filter prevents dangerous system calls.

**Messaging-Integrated Team Assistant:** A distributed team deploys NemoClaw with Telegram and Slack bridges. Team members interact with the agent through their existing messaging tools. The agent processes requests in the sandbox, and the messaging bridges (running on the host) forward responses. Provider credentials stay on the host, outside the agent's reach.
