## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
<!-- references:
- [NemoClaw Overview](https://docs.nvidia.com/nemoclaw/latest/about/overview.html) | official-docs
- [NemoClaw Deployment Guide](https://docs.nvidia.com/nemoclaw/latest/deployment/deploy-remote.html) | official-docs
- [NemoClaw Telegram Bridge](https://docs.nvidia.com/nemoclaw/latest/deployment/telegram-bridge.html) | official-docs
-->

### When to Use It

**Always-on coding assistants in production or staging environments.** If your team wants an AI agent that continuously monitors a codebase, responds to messages on Slack or Telegram, and can execute code -- but you need guarantees that it cannot exfiltrate secrets or make unauthorized network calls -- NemoClaw provides the isolation and policy controls to make this viable. Think of it as the difference between hiring a contractor who works in your office (open network) versus one who works in a controlled facility (sandboxed environment).

**Sandboxed agent testing before granting broader permissions.** Before giving an AI agent access to production APIs, you can use NemoClaw to run it in a deny-by-default network environment and observe what endpoints it tries to reach. The approval workflow lets you incrementally grant access as you build trust -- like a probation period for a new employee where each new access request requires manager approval.

**Private inference with sensitive codebases.** When working with proprietary code that cannot leave your infrastructure, NemoClaw's local inference support (Ollama, NVIDIA NIM, vLLM) means model calls never leave your network. Combined with the sandbox's filesystem isolation, this provides a layered privacy guarantee -- like a vault within a vault, where even if someone reaches the outer room, the inner contents remain protected.

**Remote GPU deployment for persistent AI assistants.** NemoClaw supports deploying sandboxed agents to remote GPU instances (currently via Brev as an experimental feature). This suits teams that want always-on agents running on dedicated hardware without direct SSH access to the host machine.

**Multi-channel AI assistants with unified security.** Through its messaging bridges for Telegram, Discord, and Slack, NemoClaw lets an AI assistant be accessible from multiple channels while maintaining a single security boundary. All messages route through the same sandboxed agent with the same network policies, regardless of which channel they arrived from.

### When NOT to Use It

**Quick, interactive coding sessions.** If you just want to chat with an AI about code for a few minutes, NemoClaw's setup overhead (onboarding wizard, sandbox image download, container startup) is unnecessary. Plain OpenClaw without NemoClaw is faster for ad-hoc use.

**Windows or macOS as the primary development platform.** While NemoClaw supports macOS via Colima/Docker Desktop and Windows via WSL, it is fundamentally a Linux-first tool. The kernel-level isolation mechanisms (Landlock, seccomp, network namespaces) are Linux-native, and the experience on other platforms involves additional layers of virtualization that add complexity and reduce performance.

**Production workloads (as of March 2026).** NemoClaw is explicitly labeled as alpha software. APIs, configuration schemas, and runtime behavior may change without notice. Using it for production-critical workflows creates risk of breakage during upgrades.

**Environments requiring fine-grained per-file permissions.** NemoClaw's filesystem policy is coarse: the agent can read-write `/sandbox` and `/tmp`, and everything else is read-only. If you need the agent to have write access to some files in a directory but not others, you would need to structure your workspace accordingly rather than relying on NemoClaw's built-in policies.

**Teams without container infrastructure.** NemoClaw requires Docker (or a compatible container runtime). Teams that have not adopted containers will face the overhead of setting up and maintaining Docker in addition to NemoClaw itself.

### Real-World Examples

**Enterprise code review assistant.** An organization runs a NemoClaw-sandboxed OpenClaw agent connected to their Slack workspace. Developers send code snippets and questions via Slack messages. The agent can access the team's private GitHub repositories (allowed in the network policy) and respond with reviews, but it cannot reach any other external services without operator approval. This provides a persistent, team-accessible AI reviewer with controlled data boundaries.

**Secure research environment.** A research lab working with sensitive data uses NemoClaw with local Ollama inference so that no model calls leave their network. The agent assists researchers with data analysis code, running entirely within the lab's infrastructure. The deny-by-default network policy ensures that even if a researcher asks the agent to "upload results to a cloud service," the request is blocked and flagged for review.

**DevOps automation with human-in-the-loop.** A platform team runs a NemoClaw agent that monitors infrastructure logs and suggests remediation steps. The agent can read monitoring dashboards (allowed endpoints) but cannot execute infrastructure changes without the operator approving the network requests first. This provides AI-assisted incident response with a mandatory human checkpoint before any action is taken.
