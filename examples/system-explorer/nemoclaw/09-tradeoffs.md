## Trade-offs & Limitations
<!-- level: intermediate -->
<!-- references:
- [NVIDIA NemoClaw: Engineering Autonomy Within Enterprise Guardrails](https://hyperframeresearch.com/2026/03/24/nvidia-nemoclaw-engineering-autonomy-within-enterprise-guardrails/) | blog
- [NemoClaw vs Docker Isolation](https://www.katonic.ai/blog/nemoclaw-docker-isolation) | blog
- [OpenClaw vs NemoClaw](https://repello.ai/blog/openclaw-vs-nemoclaw) | blog
- [Nvidia Details NemoClaw Security Guardrails](https://www.sdxcentral.com/news/nvidia-details-nemoclaw-security-guardrails-in-wake-of-ai-agent-concerns/) | blog
-->

### Strengths

**Infrastructure-Level Security:** The defining advantage. Security policies are enforced at the OS/kernel level (Landlock, seccomp, network namespaces), not at the prompt level. A compromised or adversarial agent cannot override these restrictions because they exist outside its execution environment. This is a fundamentally stronger security model than in-agent guardrails.

**One-Command Deployment:** The onboarding wizard takes you from zero to a fully sandboxed, policy-enforced agent in a single `nemoclaw onboard` command. The blueprint system handles all the complexity of configuring Docker, OpenShell, policies, and inference routing.

**Privacy Router:** The ability to route inference requests between local and cloud models based on policy is a genuine differentiator. Most agent frameworks send everything to a cloud API. NemoClaw's privacy router gives enterprises a path to use powerful AI agents without sending sensitive data off-premises.

**Layered Defense:** Four independent enforcement layers (network, filesystem, process, inference) provide defense in depth. Compromising one layer doesn't give access to the others. Filesystem and process restrictions are immutable after sandbox creation, preventing runtime weakening.

**Hot-Reloadable Policies:** Network and inference policies can be updated without restarting the agent, enabling operational flexibility. Operators can iteratively refine the allowlist based on observed agent behavior.

**Open Source:** Apache 2.0 license with an active GitHub community (18,000+ stars). The code is auditable, and the security model can be verified independently.

### Limitations

**Alpha Software:** NemoClaw is explicitly not production-ready. APIs, configuration schemas, and runtime behavior are subject to breaking changes. Depending on alpha software for critical workflows is risky. Plan for instability and migration costs.

**OpenClaw-Only:** NemoClaw is tightly coupled to OpenClaw. If you use Claude Code, Cursor, Windsurf, or another agent, you cannot use NemoClaw -- you'd use OpenShell directly, which requires more manual configuration.

**Linux-First:** Full support requires Linux (Ubuntu 22.04+). macOS support exists through Docker Desktop or Colima but adds complexity. Windows requires WSL. There is no native Windows or macOS support, limiting adoption in developer environments where these are the primary OS.

**Single-Sandbox Scope:** NemoClaw manages one sandbox at a time. If you need to govern multiple agents, teams, and environments with centralized policy management and audit, you need an orchestration layer above NemoClaw. Fleet management is not in scope.

**Resource Requirements:** 8 GB RAM minimum, 20 GB disk, and a 2.4 GB container image make NemoClaw impractical on lightweight machines, cloud VPS instances with limited resources, or low-power development environments.

**Compaction Vulnerability:** In long agent sessions, context window compaction can cause the agent to deprioritize or lose track of policy updates, stop commands, or authorization revocations issued during the session. This is a known limitation of the agent architecture that NemoClaw cannot fully solve -- it mitigates the risk through infrastructure enforcement, but the agent's in-context behavior may still drift.

**Operational Maturity Required:** NemoClaw's YAML-based policy model requires understanding network security, container isolation, and agent behavior patterns. Organizations without DevOps or platform engineering expertise will struggle to configure and maintain policies effectively.

**Local Inference is Experimental:** Running Nemotron or other models locally via Ollama or vLLM is marked as experimental. Local inference on macOS is particularly unstable. If your privacy requirements demand local-only inference, be prepared for limitations.

### Alternatives Comparison

| Dimension | NemoClaw | OpenShell (Direct) | Docker Isolation | NeMo Guardrails | E2B Sandboxes |
|-----------|----------|-------------------|-----------------|----------------|---------------|
| Security Model | Infrastructure-level (kernel) | Infrastructure-level (kernel) | Container-level | Prompt-level | Container-level |
| Agent Support | OpenClaw only | Multiple (Claude Code, Cursor, etc.) | Any | Any LLM | Any |
| Setup Complexity | One command | Manual configuration | Manual | Code integration | API-based |
| Privacy Routing | Built-in | Built-in | None | None | None |
| Policy Granularity | Network + FS + Process + Inference | Network + FS + Process + Inference | Container boundaries | Topic + Output | Container boundaries |
| Hot-Reload Policies | Yes (network, inference) | Yes (network, inference) | No | Yes | No |
| Production Ready | No (alpha) | No (alpha) | Yes | Yes | Yes |
| Self-Hosted | Yes | Yes | Yes | Yes | Cloud or self-hosted |

### When Each Alternative is Better

**OpenShell (Direct):** When you use an agent other than OpenClaw. OpenShell provides the same security primitives but requires manual configuration instead of NemoClaw's automated blueprint.

**Docker Isolation Alone:** When you need basic process isolation without agent-aware policy enforcement, and you're comfortable managing security through standard container best practices (non-root users, read-only filesystems, network policies).

**NeMo Guardrails:** When your threat model is about controlling LLM output quality (preventing off-topic responses, enforcing conversation flows, filtering harmful content) rather than controlling agent infrastructure access. NeMo Guardrails and NemoClaw address different layers and can be combined.

**E2B Sandboxes:** When you need lightweight, ephemeral sandboxes for code execution (not long-running agents) and want a cloud-hosted solution with minimal operational overhead.

### Honest Assessment

NemoClaw solves a real problem -- infrastructure-level security for autonomous AI agents -- with a technically sound approach. Out-of-process policy enforcement is the right architecture for this threat model, and the privacy router addresses a genuine enterprise concern. However, the alpha status, OpenClaw-only focus, and Linux-first requirements significantly limit its current applicability. For most teams in 2026, NemoClaw is worth evaluating and experimenting with, but production deployment should wait for a stable release. The biggest risk is not technical but organizational: even with perfect infrastructure security, the value of NemoClaw depends on teams having the operational maturity to write and maintain effective security policies.
