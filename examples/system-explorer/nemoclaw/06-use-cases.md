## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
<!-- references:
- [NVIDIA NemoClaw Product Page](https://www.nvidia.com/en-us/ai/nemoclaw/) | official-docs
- [NemoClaw: NVIDIA's Open Source Stack for Running AI Agents You Can Actually Trust](https://dev.to/arshtechpro/nemoclaw-nvidias-open-source-stack-for-running-ai-agents-you-can-actually-trust-50gl) | blog
- [OpenClaw Alternatives for Enterprise Security](https://dev.to/sebastian_chedal/openclaw-alternatives-for-enterprise-security-honest-2026-comparison-3oa2) | blog
-->

### When to Use NemoClaw

NemoClaw addresses a specific set of deployment scenarios where autonomous AI agents need to operate with reduced risk. Here are the primary use cases:

### 1. Enterprise Agent Deployment

**Scenario:** A company has been running OpenClaw agents internally for developer productivity — answering questions, writing code, managing tickets. Now they want to expand to production use but need security controls that satisfy their InfoSec team.

**How NemoClaw helps:** NemoClaw adds network egress controls, filesystem isolation, and managed inference routing without requiring the team to rewrite their existing OpenClaw configuration. The agent's learned skills and session history carry over. The InfoSec team gets audit visibility into every outbound connection and API call the agent makes, with real-time approval workflows for new endpoints.

### 2. Always-On Personal Assistants on Dedicated Hardware

**Scenario:** A researcher or power user wants to run an autonomous AI assistant 24/7 on their NVIDIA DGX Spark or DGX Station, handling tasks like monitoring research papers, managing email, and running data analysis pipelines — all while keeping sensitive data local.

**How NemoClaw helps:** NemoClaw configures the agent to use local Nemotron models for sensitive queries (data never leaves the machine) while routing non-sensitive queries to cloud models for better capability. The sandbox prevents the agent from accessing files outside its designated workspace, even when running unattended for extended periods.

### 3. Multi-Agent Development Environments

**Scenario:** A platform team is building internal tooling where multiple AI agents collaborate on tasks — one agent writes code, another reviews it, a third deploys it. Each agent needs different access levels and should not be able to interfere with the others.

**How NemoClaw helps:** Each agent runs in its own sandbox with independent network policies, filesystem boundaries, and inference configurations. One agent can be allowed access to GitHub while another is restricted to internal services only. The blueprint-based approach ensures every sandbox is reproducible and auditable.

### 4. Compliance-Sensitive Environments

**Scenario:** A financial services firm wants to use AI agents for internal operations but must demonstrate to regulators that agents cannot exfiltrate customer data or make unauthorized external connections.

**How NemoClaw helps:** The deny-all-by-default network policy, combined with Landlock filesystem restrictions and seccomp syscall filtering, provides a defense-in-depth posture that can be documented for compliance audits. Every blocked connection attempt is logged with full context (host, port, requesting process). The operator approval workflow creates an auditable trail of all policy exceptions.

### 5. Secure Evaluation and Red-Teaming

**Scenario:** A security team wants to evaluate the behavior of AI agents under adversarial conditions — testing prompt injection attacks, tool misuse, and privilege escalation attempts — without risking the host system.

**How NemoClaw helps:** The sandbox provides a controlled environment where agents can be tested against attack scenarios. Even if a prompt injection successfully instructs the agent to attempt data exfiltration or privilege escalation, the kernel-level security controls prevent the actions from succeeding. The policy engine logs all blocked attempts, providing detailed telemetry for security analysis.

### When NOT to Use NemoClaw

NemoClaw is not the right choice for every situation:

- **Quick experimentation:** If you are just trying out OpenClaw for the first time, the overhead of sandbox creation and policy management adds friction. Plain OpenClaw is better for exploration and learning.
- **Cross-platform needs:** NemoClaw's full security stack is Linux-only. macOS and Windows WSL support exists but with reduced security guarantees (no Landlock on macOS, limited namespace isolation on WSL).
- **Latency-sensitive applications:** The inference routing through the OpenShell gateway adds a small amount of latency compared to direct API calls. For latency-critical real-time applications, this overhead may be unacceptable.
- **Lightweight chatbots:** If your agent only answers questions and never executes code or accesses external services, the security overhead of NemoClaw provides little benefit over a simpler deployment.
