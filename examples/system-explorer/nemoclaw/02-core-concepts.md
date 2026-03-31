## Core Concepts
<!-- level: beginner -->
<!-- references:
- [NemoClaw Architecture Reference](https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html) | official-docs
- [How NemoClaw Works](https://docs.nvidia.com/nemoclaw/latest/about/how-it-works.html) | official-docs
- [Run Autonomous Agents More Safely with NVIDIA OpenShell](https://developer.nvidia.com/blog/run-autonomous-self-evolving-agents-more-safely-with-nvidia-openshell/) | blog
-->

NemoClaw is built on six core concepts. Understanding them gives you the vocabulary to reason about how autonomous AI agents can be run more safely, why NemoClaw separates the control plane from the agent process, and how each security layer reinforces the others.

### 1. OpenShell Sandbox

**Definition:** An OpenShell sandbox is an isolated Linux container environment where the OpenClaw agent runs. It uses kernel-level isolation primitives — Landlock for filesystem access control, seccomp for syscall filtering, and network namespaces for network isolation — to confine the agent's capabilities.

**Analogy:** Think of a bank vault with a one-way intercom. The agent can work freely inside the vault (run code, process data), but every request to access something outside — a website, a file, a model — must go through the intercom (OpenShell gateway) where a guard (the operator) decides whether to allow it.

**Why it matters:** Autonomous agents can execute arbitrary code, install packages, and reach external services. Without isolation, a compromised or misbehaving agent has the same access as the user who launched it. The sandbox ensures that even if an agent attempts something unauthorized, the kernel-level controls prevent it from succeeding.

### 2. Blueprint

**Definition:** The blueprint is a versioned Python artifact that contains the complete specification for creating a NemoClaw sandbox — including the Dockerfile, security policies, capability drops, network rules, and inference configuration. It is the reproducible "recipe" for a hardened agent environment.

**Analogy:** A blueprint is like an architect's building plan. It specifies exactly how the sandbox should be constructed — which walls go where (filesystem boundaries), which doors exist (network egress rules), and what equipment is installed (inference providers). Re-running the blueprint on a different machine produces an identical sandbox.

**Why it matters:** Reproducibility is essential for security. If every sandbox is built from the same immutable, digest-verified blueprint, you can audit exactly what is running and guarantee that no unauthorized modifications have been introduced. The blueprint lifecycle (resolve, verify, plan, apply, status) ensures supply-chain integrity at every step.

### 3. Inference Routing

**Definition:** NemoClaw routes all model API calls through the OpenShell gateway. The agent inside the sandbox communicates with a local endpoint (`inference.local`), and OpenShell transparently forwards those requests to the configured provider (NVIDIA Endpoints, OpenAI, Anthropic, Google Gemini, or a local model like Ollama). The agent never sees raw API credentials.

**Analogy:** Imagine ordering food through a concierge desk at a hotel. You tell the concierge what you want (an inference request), and they call the restaurant (the model provider) using the hotel's account. You get your food, but you never see the hotel's credit card number. If the concierge decides a particular restaurant is off-limits, your order simply does not go through.

**Why it matters:** API keys are high-value secrets. If an agent had direct access to provider credentials, a prompt injection or code execution exploit could exfiltrate them. By keeping credentials on the host and routing inference through the gateway, NemoClaw ensures that compromising the agent does not compromise your API keys.

### 4. Network Policy Engine

**Definition:** The network policy engine controls all outbound (egress) connections from the sandbox. A baseline policy file (`openclaw-sandbox.yaml`) denies all traffic by default, then explicitly allows connections to approved endpoints. When the agent attempts to reach an unlisted host, OpenShell blocks the connection and surfaces it in the terminal UI for operator approval.

**Analogy:** Think of a corporate firewall with a "deny all" default rule. Every new destination the agent wants to reach triggers a notification to the security team. They can approve it for the current session or add it to the permanent allowlist. The agent cannot bypass this — it lives in a separate network namespace and physically cannot see the host's network interfaces.

**Why it matters:** Autonomous agents interact with external services — fetching web pages, calling APIs, downloading packages. Without egress controls, an agent could exfiltrate data to an attacker-controlled server or connect to malicious endpoints. The network policy engine provides real-time visibility and control over every outbound connection.

### 5. Plugin / Blueprint Separation

**Definition:** NemoClaw is architecturally split into two components: a thin TypeScript plugin that runs in-process with the OpenClaw CLI and handles user interaction, and a versioned Python blueprint that contains all orchestration logic. The plugin remains stable across releases while the blueprint evolves independently.

**Analogy:** The plugin is like a car's steering wheel and dashboard — the interface you interact with. The blueprint is like the engine and drivetrain — the machinery that actually does the work. You can upgrade the engine (blueprint) without redesigning the dashboard (plugin), and the steering wheel always feels the same regardless of what engine is installed.

**Why it matters:** This separation enables independent versioning and safe upgrades. The plugin can validate blueprint versions, verify digests, and enforce compatibility constraints before executing any changes. It also means the surface area of code running in the privileged host context (plugin) is minimal, while the complex orchestration logic (blueprint) runs in a controlled subprocess.

### 6. State Management and Persistence

**Definition:** NemoClaw manages host-side state for credentials, sandbox metadata, and OpenClaw configuration snapshots. It supports secure migration of agent state across machines, with credential stripping and integrity checks to ensure sensitive data does not leak during transfers.

**Analogy:** Think of a diplomat's secure briefcase with a tamper-evident seal. When moving an agent's state from one machine to another, NemoClaw strips out sensitive credentials (like removing classified documents before transit), seals the remaining configuration (integrity hash), and re-provisions credentials on the destination machine.

**Why it matters:** Production agent deployments need to survive machine restarts, hardware migrations, and scaling events. State management ensures that the agent's learned behaviors, session history, and configuration can be reliably transferred without exposing secrets or corrupting the sandbox's security posture.
