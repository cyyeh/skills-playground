# System Analysis: NemoClaw

## Metadata
- **Name:** NemoClaw
- **Category:** AI Agent Security & Orchestration Runtime
- **Official URL:** [https://www.nvidia.com/en-us/ai/nemoclaw/](https://www.nvidia.com/en-us/ai/nemoclaw/)
- **GitHub:** [https://github.com/NVIDIA/NemoClaw](https://github.com/NVIDIA/NemoClaw)
- **Tag:** alpha (early preview)
- **License:** Apache License 2.0
- **Latest Version:** Alpha Preview (released March 16, 2026)
- **Analysis Date:** 2026-03-28

---

## Overview
<!-- level: beginner -->
<!-- references: https://docs.nvidia.com/nemoclaw/latest/index.html, https://github.com/NVIDIA/NemoClaw, https://nvidianews.nvidia.com/news/nvidia-announces-nemoclaw, https://dev.to/arshtechpro/nemoclaw-nvidias-open-source-stack-for-running-ai-agents-you-can-actually-trust-50gl -->

### What It Is

[NemoClaw](https://github.com/NVIDIA/NemoClaw) is an open-source reference stack from NVIDIA that provides security, privacy, and operational guardrails for running autonomous AI agents built on the [OpenClaw](https://github.com/openclaw/openclaw) platform. It wraps OpenClaw assistants ("claws") inside the [NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell) runtime -- a sandboxed execution environment that enforces policy-based controls over network access, filesystem permissions, process execution, and inference routing. NemoClaw was announced at [GTC 2026](https://blogs.nvidia.com/blog/rtx-ai-garage-gtc-2026-nemoclaw/) on March 16, 2026.

In concrete terms, NemoClaw takes a single `curl | bash` command and produces: a sandboxed container running an OpenClaw agent, an inference gateway routing model calls to local or cloud providers, a deny-by-default network policy, and an operator terminal for approving or blocking the agent's requests in real time.

### Who It's For

- **Enterprise teams** deploying always-on AI assistants who need compliance-grade isolation (SOC 2, data residency)
- **Developers** who want to experiment with autonomous agents without granting them unchecked system access
- **Security engineers** evaluating agent sandboxing solutions after incidents like the [ClawHavoc supply-chain attack](https://cyberpress.org/clawhavoc-poisons-openclaws-clawhub-with-1184-malicious-skills/) (February 2026)
- **Organizations** wanting local inference with NVIDIA Nemotron models for privacy-sensitive workloads

### The One-Sentence Pitch

NemoClaw lets you run powerful, always-on AI agents with a single command while keeping them locked inside a policy-enforced sandbox where every network request, file write, and model call is controlled and auditable.

---

## Core Concepts
<!-- level: beginner -->
<!-- references: https://docs.nvidia.com/nemoclaw/latest/about/how-it-works.html, https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html, https://stormap.ai/post/inside-nemoclaw-the-architecture-sandbox-model-and-security-tradeoffs -->

### 1. Sandbox

**Definition:** An isolated container environment where the OpenClaw agent runs, restricted to specific filesystem paths, network endpoints, and system calls.

**Analogy:** Think of it like a bank vault with a teller window. The agent (teller) can interact with the outside world, but only through approved channels -- it cannot walk out the vault door, access the back office, or make phone calls without authorization.

**Why it matters:** Autonomous agents that can write code, spawn sub-agents, and persist across sessions create security risks that traditional containers do not fully address. The sandbox moves enforcement outside the agent entirely, so even a compromised agent cannot override its own restrictions.

### 2. Blueprint

**Definition:** A versioned, cryptographically verified Python artifact containing all the logic for creating sandboxes, applying policies, and configuring inference. It follows a five-stage lifecycle: resolve, verify, plan, apply, status.

**Analogy:** A blueprint is like an architect's sealed building plan. Before construction (sandbox creation) begins, the plan is verified against a tamper-proof seal (cryptographic digest). The builder (OpenShell) then executes it exactly as specified -- no improvisation allowed.

**Why it matters:** Blueprint versioning ensures reproducible sandbox creation. The digest verification prevents supply-chain attacks where a malicious actor substitutes a tampered orchestration artifact -- a real concern given the [ClawHavoc incident](https://securityboulevard.com/2026/02/securing-openclaw-againstclawhavoc/) that poisoned OpenClaw's skill registry.

### 3. OpenShell Runtime

**Definition:** NVIDIA's secure runtime environment (part of the [NVIDIA Agent Toolkit](https://www.nvidia.com/en-us/ai/nemoclaw/)) that provides kernel-level isolation using Landlock LSM, seccomp syscall filtering, and network namespace isolation.

**Analogy:** OpenShell is the prison warden. The sandbox is the cell, the policies are the rulebook, and OpenShell enforces every rule at the physical (kernel) level. It does not trust the inmate (agent) to self-regulate.

**Why it matters:** Security controls must be mathematical runtime properties, not model personality traits. OpenShell enforces isolation at the OS kernel level, which means no amount of prompt injection or agent cleverness can bypass the restrictions.

### 4. Network Policy

**Definition:** Declarative YAML rules governing which network endpoints the sandbox can reach, which binaries can access them, and which HTTP methods/paths are permitted. NemoClaw enforces deny-by-default: anything not explicitly allowed is blocked.

**Analogy:** Like a corporate firewall with a whitelist. The agent cannot call home, download packages, or exfiltrate data unless every destination is pre-approved. Unknown requests get escalated to a human operator for real-time approval.

**Why it matters:** Autonomous agents that can make HTTP requests create data exfiltration and dependency-poisoning risks. Deny-by-default network policy is the single most important containment mechanism for always-on agents.

### 5. Inference Router (Privacy Router)

**Definition:** A gateway layer that intercepts all model API calls from the sandbox and routes them to configured providers (NVIDIA Endpoints, OpenAI, Anthropic, Gemini, or local Ollama/NIM). Credentials stay on the host; the sandbox only sees `inference.local`.

**Analogy:** Like a mail room in a classified facility. Outgoing letters (inference requests) go through a central desk that stamps them with the right postage (API credentials), routes them to the correct recipient (provider), and logs every piece of correspondence. The sender never sees the postage meter or address book.

**Why it matters:** Credential isolation is critical. If an agent were compromised, it could steal API keys and make unauthorized model calls. The router keeps keys on the host side and provides a central audit point for every prompt and completion.

### 6. Plugin

**Definition:** A lightweight TypeScript module that runs within the OpenClaw CLI, registering commands (`onboard`, `connect`, `status`, `logs`) and managing blueprint lifecycle operations.

**Analogy:** The plugin is the receptionist at the front desk. It takes your request, routes it to the right department (blueprint, sandbox, policy engine), and reports back -- but it does not do the heavy lifting itself.

**Why it matters:** The plugin-blueprint separation ensures that user-facing commands remain stable even as the underlying orchestration logic evolves. Users keep muscle memory across major backend changes.

### 7. Operator Terminal (openshell term)

**Definition:** A TUI (terminal user interface) that lets operators monitor sandbox activity in real time and approve or deny blocked network requests.

**Analogy:** Like an air traffic control tower. The operator watches all outbound "flights" (requests) from the sandbox, approves cleared ones, and blocks anything suspicious -- all without the pilot (agent) being able to override the decision.

**Why it matters:** Fully autonomous agents need a human-in-the-loop escape valve. The operator terminal provides visibility and intervention capability without breaking the agent's workflow.

### How They Fit Together

The system operates in concentric layers. At the center, the **OpenClaw agent** runs inside a **sandbox**, which is built from a verified **blueprint**. The sandbox communicates with the outside world through two controlled channels: the **inference router** (for model calls) and the **network policy** (for everything else). The **OpenShell runtime** enforces all policies at the kernel level. The **plugin** provides the CLI interface, and the **operator terminal** provides real-time human oversight. Every layer reinforces the others -- there is no single point of failure in the security model.

---

## Architecture
<!-- level: intermediate -->
<!-- references: https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html, https://deepwiki.com/NVIDIA/NemoClaw, https://stormap.ai/post/inside-nemoclaw-the-architecture-sandbox-model-and-security-tradeoffs, https://github.com/NVIDIA/NemoClaw -->

### High-Level Design

NemoClaw implements a **plugin-blueprint architecture** that separates concerns into a thin, stable CLI layer and a versioned orchestration layer:

```
Host Environment
├── nemoclaw CLI (TypeScript plugin)
│   ├── bin/nemoclaw.js              # Entry point
│   ├── src/cli.ts                   # Commander.js subcommand wiring
│   ├── src/commands/                # launch, connect, status, logs, slash
│   └── src/blueprint/              # resolve, fetch, verify, exec, state
├── Blueprint Resolver
│   └── Validates version + digest before execution
├── OpenShell Gateway
│   ├── Inference routing (inference.local → provider)
│   ├── Credential management (host-side)
│   └── Policy enforcement
└── Docker Runtime

Sandbox Environment (container)
├── OpenClaw Agent
├── NemoClaw Plugin (in-sandbox instance)
├── Inference endpoint (inference.local)
├── Landlock LSM (filesystem isolation)
├── seccomp (syscall filtering)
└── Network namespace (egress control)

External Services
├── NVIDIA Endpoints (integrate.api.nvidia.com)
├── OpenAI / Anthropic / Gemini APIs
├── Local Ollama / NIM instances
└── OCI registries (blueprint artifacts)
```

### Key Components

| Component | Technology | Purpose | Why It Exists |
|-----------|-----------|---------|---------------|
| **Plugin** | TypeScript, Commander.js | CLI interface for host-side operations | Provides stable UX while backend evolves; keeps plugin thin so attack surface is minimal |
| **Blueprint** | Python, YAML manifest | Orchestration logic for sandbox creation | Versioned and digest-verified to prevent supply-chain attacks; decoupled from plugin for independent release cycles |
| **Sandbox** | Docker + Landlock + seccomp + netns | Isolated agent execution environment | Kernel-level enforcement ensures even compromised agents cannot escape; defense-in-depth across filesystem, network, process, and inference |
| **OpenShell Gateway** | Part of NVIDIA Agent Toolkit | Policy enforcement and inference routing | Central choke point for all external communication; enables credential isolation and audit logging |
| **Policy Engine** | YAML declarations | Network and filesystem access rules | Declarative configuration is auditable, version-controllable, and reviewable -- unlike imperative security scripts |
| **Inference Router** | HTTP proxy (gateway) | Model API routing with credential injection | Prevents agents from accessing raw API keys; enables runtime provider switching without agent code changes |
| **Operator Terminal** | TUI (openshell term) | Real-time monitoring and approval | Human-in-the-loop for edge cases; prevents approval fatigue through persistent session rules |

### Data Flow

**Inference Request Path:**
```
OpenClaw Agent (inside sandbox)
  │ model.complete("What is the weather?")
  ▼
NemoClaw Provider Plugin (src/index.ts)
  │ HTTP POST to inference.local
  ▼
OpenShell Gateway (host-side)
  │ Policy validation → credential injection → routing
  ▼
Upstream Provider (NVIDIA Cloud / OpenAI / local Ollama)
  │ Response
  ▼
Gateway → Plugin → Agent
```
<!-- source: https://deepwiki.com/NVIDIA/NemoClaw -->

**Network Egress Path (non-inference):**
```
Agent attempts HTTP request to api.slack.com
  │
  ▼
Network namespace intercepts request
  │
  ▼
Policy check: is api.slack.com in allowed endpoints?
  │
  ├── YES → Request proceeds
  └── NO  → Request blocked; operator prompted in TUI
              │
              ├── Operator approves → Request proceeds (session-scoped)
              └── Operator denies  → Agent receives error
```

**Blueprint Execution Flow:**
```
nemoclaw onboard
  │
  ▼
1. RESOLVE  → Locate blueprint artifact, check min_openshell_version
  │              and min_openclaw_version constraints
  ▼
2. VERIFY   → Validate cryptographic digest against expected value
  │
  ▼
3. PLAN     → Determine required OpenShell resources:
  │              gateway, providers, sandbox, routing, policy
  ▼
4. APPLY    → Execute openshell CLI commands to reach desired state
  │
  ▼
5. STATUS   → Report current deployment state and health
```

### Design Decisions

**Decision: Thin Plugin, Heavy Blueprint**
The plugin handles user interaction only. All orchestration logic lives in the versioned blueprint. This means the CLI remains stable across major architectural changes, and blueprints can be independently released, verified, and rolled back. The trade-off is an extra artifact to manage, but the security and stability benefits justify it.

**Decision: Deny-by-Default Networking**
Every outbound connection is blocked unless explicitly whitelisted. This is more restrictive than typical container networking but essential for autonomous agents that can write their own HTTP requests. The trade-off is operational friction -- operators must approve new endpoints -- but the alternative (allow-by-default) is unacceptable for always-on agents.

**Decision: Credential Separation**
API keys never enter the sandbox. The gateway injects credentials at the routing layer. This means a sandbox compromise cannot leak provider credentials. The trade-off is that inference always goes through the gateway (adding latency), but the security benefit is absolute.

**Decision: Kernel-Level Enforcement**
Rather than relying on application-level sandboxing (which agents can potentially bypass), NemoClaw uses Landlock LSM, seccomp, and network namespaces -- kernel mechanisms that are immune to application-layer exploits. The trade-off is Linux-first support (macOS/Windows require Docker Desktop with its own overhead).

---

## How It Works
<!-- level: intermediate -->
<!-- references: https://docs.nvidia.com/nemoclaw/latest/about/how-it-works.html, https://docs.nvidia.com/nemoclaw/latest/network-policy/customize-network-policy.html, https://docs.nvidia.com/nemoclaw/latest/reference/inference-profiles.html -->

### Sandbox Creation (Onboarding)

The `nemoclaw onboard` command triggers a wizard that creates the full stack in one pass:

1. **Blueprint download:** The plugin resolves the latest compatible blueprint from an OCI registry, then verifies its cryptographic digest
2. **Resource planning:** The blueprint's runner determines which OpenShell resources to create -- gateway, inference providers, sandbox container, network policy, and inference route
3. **OpenShell provisioning:** The plan executes via `openshell` CLI commands, pulling the sandbox image (`ghcr.io/nvidia/openshell-community/sandboxes/openclaw`, approximately 2.4 GB compressed)
4. **Policy application:** The baseline `openclaw-sandbox.yaml` policy is applied, establishing deny-by-default networking and restricted filesystem access
5. **Inference configuration:** The selected provider (NVIDIA, OpenAI, Anthropic, Gemini, or local Ollama) is registered with the gateway, credentials stored host-side in `~/.nemoclaw/credentials.json`

After onboarding, the agent runs inside the sandbox with all isolation layers active.

### Policy Enforcement Mechanism

NemoClaw enforces a two-tier policy model:

| Layer | Enforcement | Mutability |
|-------|-------------|------------|
| **Filesystem / Process** | Landlock LSM, seccomp, capability drops | Locked at creation time -- immutable |
| **Network / Inference** | Network namespace, gateway routing | Hot-reloadable at runtime |

This distinction is critical. Filesystem and process restrictions are set once and cannot be changed without destroying and recreating the sandbox. Network and inference policies can be updated dynamically:

```bash
# Apply a preset policy to allow Slack access on a running sandbox
openshell policy set nemoclaw-blueprint/policies/presets/slack.yaml
```
<!-- source: https://docs.nvidia.com/nemoclaw/latest/network-policy/customize-network-policy.html -->

Dynamic changes are session-scoped: when the sandbox stops, the running policy resets to the baseline.

### Inference Routing Mechanism

Inference requests from the agent never leave the sandbox directly. The flow is:

1. Agent calls `model.complete()` which targets `inference.local`
2. The NemoClaw provider plugin intercepts the call and makes an HTTP POST to the gateway
3. The OpenShell gateway validates the request against policy
4. The gateway injects the real provider credentials (stored host-side)
5. The request is forwarded to the configured upstream (NVIDIA Endpoints, OpenAI, etc.)
6. The response flows back through the same path

Provider validation during onboarding differs by type:
- **OpenAI-compatible:** Tests `/responses` first, then `/chat/completions`
- **Anthropic-compatible:** Validates against `/v1/messages`
- **NVIDIA Endpoints:** Checks model names via `integrate.api.nvidia.com/v1/models`
- **Local Ollama:** Pulls, warms, and validates models during setup

Providers can be switched at runtime without restarting the sandbox:
```bash
openshell inference set --provider openai --model gpt-4o
```

### Security Layer Stack

NemoClaw applies five protection layers, each addressing a different threat vector:

1. **Container Isolation:** Docker with a hardened base image (multi-stage build, minimal attack surface)
2. **Process Hardening:** Capability drops in `nemoclaw-start.sh`, seccomp syscall filtering blocks dangerous operations like `ptrace`, `mount`, `reboot`
3. **Filesystem Integrity:** Config files owned by root with SHA256 hash verification; agents write only to `/sandbox` and `/tmp`; system paths are read-only Landlock-enforced
4. **Network Control:** Deny-by-default egress policy; unapproved requests surface to operator TUI for approval; SSRF validation in `ssrf.ts` prevents server-side request forgery
5. **Inference Security:** Credentials never enter sandbox; all model calls routed through gateway; provider switching controlled by host-side commands

### Performance Characteristics

- **Sandbox startup:** Approximately 30-60 seconds for initial onboarding (blueprint download, image pull, resource creation); subsequent starts are faster with cached images
- **Inference latency:** Gateway routing adds a small overhead (single-digit milliseconds for local routing) compared to direct API calls; this is the cost of credential isolation
- **Disk footprint:** ~2.4 GB compressed for the sandbox image, plus model weights if running local inference (Nemotron 3 Nano 4B requires ~8 GB, Nemotron 3 Super 120B requires 128+ GB)
- **Memory requirements:** 8 GB minimum (16 GB recommended); local inference with large models requires substantially more

---

## Implementation Details
<!-- level: advanced -->
<!-- references: https://docs.nvidia.com/nemoclaw/latest/get-started/quickstart.html, https://github.com/NVIDIA/NemoClaw, https://docs.nvidia.com/nemoclaw/latest/reference/commands.html, https://docs.nvidia.com/nemoclaw/latest/network-policy/customize-network-policy.html -->

### Getting Started

**Prerequisites:**
- Ubuntu 22.04 LTS or later (primary); macOS via Colima/Docker Desktop; Windows via WSL + Docker Desktop
- Node.js 22.16+, npm 10+
- Docker (primary container runtime)
- 4+ vCPU, 16 GB RAM (recommended), 40 GB free disk

**Installation (single command):**
```bash
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash
```
<!-- source: https://docs.nvidia.com/nemoclaw/latest/get-started/quickstart.html -->

The installer handles Node.js installation if needed, runs the interactive onboarding wizard, and creates a sandboxed OpenClaw instance with your chosen inference provider and security policies.

**First interaction with your agent:**
```bash
# Connect to the sandbox shell
nemoclaw my-assistant connect

# Interactive chat (TUI mode)
openclaw tui

# Single message (CLI mode)
openclaw agent --agent main --local -m "hello" --session-id test
```
<!-- source: https://docs.nvidia.com/nemoclaw/latest/get-started/quickstart.html -->

**Monitor and manage:**
```bash
# Check sandbox health
nemoclaw my-assistant status

# Stream logs
nemoclaw my-assistant logs --follow

# Open operator terminal for request approval
openshell term

# List all sandboxes
nemoclaw list
```

### Configuration Essentials

**Host-side state files:**
```
~/.nemoclaw/credentials.json     # Provider API keys (0o600 permissions)
~/.nemoclaw/sandboxes.json       # Sandbox metadata and applied policies
~/.openclaw/openclaw.json        # Host OpenClaw configuration
```
<!-- source: https://github.com/NVIDIA/NemoClaw -->

**Baseline network policy** (`nemoclaw-blueprint/policies/openclaw-sandbox.yaml`):
```yaml
# Deny-by-default network policy
# Each entry defines: endpoints, binaries, and rules
network:
  - name: inference
    endpoints:
      - host: inference.local
        port: 443
    binaries:
      - /usr/bin/node
    rules:
      - methods: [POST]
        paths: ["/v1/*", "/responses"]
  # Additional entries for required system endpoints
```
<!-- source: https://docs.nvidia.com/nemoclaw/latest/network-policy/customize-network-policy.html -->

**Adding a preset policy (e.g., Slack integration):**
```bash
# Dynamic (session-scoped, resets on sandbox stop)
openshell policy set nemoclaw-blueprint/policies/presets/slack.yaml

# Or via CLI
nemoclaw my-assistant policy-add
```

Available presets include: discord, docker, huggingface, jira, npm, outlook, pypi, slack, and telegram.

**Switching inference providers at runtime:**
```bash
# No sandbox restart required
openshell inference set --provider anthropic --model claude-sonnet-4-20250514
```
<!-- source: https://docs.nvidia.com/nemoclaw/latest/reference/inference-profiles.html -->

### Code Patterns

**Plugin entry point** (`nemoclaw/src/index.ts`):
The plugin registers as an OpenClaw provider, intercepting inference calls and routing them through the OpenShell gateway. It registers the `/nemoclaw` slash command for in-chat status queries.

```typescript
// Simplified inference routing pattern
// source: https://github.com/NVIDIA/NemoClaw/blob/main/nemoclaw/src/index.ts
// (lines ~178-202, simplified)

async function routeInference(request: InferenceRequest): Promise<InferenceResponse> {
  // Agent code targets inference.local -- never the real provider
  const gatewayUrl = "https://inference.local/v1/chat/completions";

  // POST to the OpenShell gateway, which injects real credentials
  const response = await fetch(gatewayUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  return response.json();
}
```

**Blueprint manifest** (`nemoclaw-blueprint/blueprint.yaml`):
```yaml
# Blueprint version and compatibility constraints
# source: https://github.com/NVIDIA/NemoClaw/tree/main/nemoclaw-blueprint
version: "0.1.0"
min_openshell_version: "0.4.0"
min_openclaw_version: "2026.1.0"
digest: "sha256:abc123..."  # Computed at release time

inference_profiles:
  - name: nvidia
    type: openai-compatible
    endpoint: integrate.api.nvidia.com
  - name: openai
    type: openai-native
  - name: anthropic
    type: anthropic-native
  - name: ollama
    type: openai-compatible
    endpoint: localhost:11434
```

**SSRF protection** (`nemoclaw/src/ssrf.ts`):
The plugin includes server-side request forgery validation that checks IP addresses and DNS resolution before allowing network requests, preventing agents from targeting internal network resources.

### Deployment Considerations

**Local development:** The default `nemoclaw onboard` path works well for single-developer setups. Choose a cloud inference provider (NVIDIA Endpoints, OpenAI, Anthropic) to minimize local resource requirements.

**Local inference (privacy-first):**
```bash
# During onboard, select Ollama provider
# NemoClaw will pull and warm the selected model
# Supported local models:
#   - Nemotron 3 Nano 4B (GeForce RTX, ~8 GB VRAM)
#   - Nemotron 3 Super 120B MoE (DGX Spark 128 GB unified memory)
#   - Qwen 3.5 variants (27B, 9B, 4B)
```

**Remote GPU deployment:**
```bash
# Deploy to a remote GPU instance via Brev (experimental)
nemoclaw deploy my-remote-assistant
```

**DGX Spark setup:**
```bash
# Apply required cgroup v2 and Docker fixes for Ubuntu 24.04
sudo nemoclaw setup-spark
```

**Uninstall:**
```bash
curl -fsSL https://raw.githubusercontent.com/NVIDIA/NemoClaw/refs/heads/main/uninstall.sh | bash
# Options: --yes (skip confirmation), --keep-openshell, --delete-models
```

---

## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
<!-- references: https://nvidianews.nvidia.com/news/nvidia-announces-nemoclaw, https://www.ai.cc/blogs/nvidia-nemoclaw-open-source-ai-agent-2026-guide/, https://repello.ai/blog/openclaw-vs-nemoclaw, https://www.nvidia.com/en-us/ai/nemoclaw/ -->

### When to Use It

- **Enterprise AI assistant deployment** where compliance requires sandboxed execution, audit trails, and data residency guarantees. If your organization handles NDAs, proprietary code, or unreleased media, NemoClaw's isolation model is designed for this.
- **Post-ClawHavoc OpenClaw hardening.** If you already run OpenClaw and want to add security without abandoning the ecosystem, NemoClaw wraps your existing setup with enterprise-grade guardrails.
- **Privacy-sensitive inference.** The privacy router can classify query sensitivity and route PII-containing requests to local Nemotron models while safe queries go to cheaper cloud providers.
- **Development sandboxing.** When building agents that write and execute code, NemoClaw prevents accidental (or malicious) damage to the host system.
- **Multi-tenant agent services.** Each sandbox is independently isolated with its own policies, enabling multiple agents with different permission levels on the same host.

### When NOT to Use It

- **Quick personal experimentation.** If you just want to try OpenClaw for 10 minutes, the 2.4 GB sandbox image download and onboarding wizard are overkill. Use vanilla OpenClaw first.
- **Non-OpenClaw agents.** NemoClaw is tightly coupled to the OpenClaw ecosystem. If you use LangChain, CrewAI, AutoGen, or other agent frameworks, NemoClaw does not support them (though OpenShell itself is more general).
- **Resource-constrained environments.** With a minimum of 4 vCPU, 8 GB RAM, and 20 GB disk (before model weights), NemoClaw is not suitable for edge devices or low-spec machines.
- **Production deployments (today).** NemoClaw is alpha software. APIs, CLI commands, and blueprint schemas are subject to breaking changes. Do not deploy it in mission-critical production systems yet.
- **Windows/macOS as primary.** Linux is the first-class platform. macOS and Windows require Docker Desktop, adding performance overhead and reducing some kernel-level isolation guarantees.

### Real-World Examples

**Post-ClawHavoc remediation:** After the [ClawHavoc supply-chain attack](https://cyberpress.org/clawhavoc-poisons-openclaws-clawhub-with-1184-malicious-skills/) (February 2026) poisoned 1,184+ skills in OpenClaw's ClawHub registry, organizations adopted NemoClaw to sandbox their OpenClaw deployments. The deny-by-default network policy prevents malicious skills from exfiltrating stolen credentials, and blueprint digest verification prevents tampered artifacts from being loaded.

**Local-first enterprise assistant:** An organization running NemoClaw on NVIDIA DGX Spark hardware with Nemotron 3 Super 120B MoE achieves fully air-gapped AI assistance -- no data leaves the local network. Sensitive queries (PII, financial data, proprietary code) are processed entirely on-premises.

**Developer workstation sandboxing:** A developer runs NemoClaw on their Ubuntu workstation with OpenAI as the inference provider. The agent can write code in `/sandbox`, but cannot access `~/.ssh`, `~/.aws`, or any other sensitive host directories. Network requests to unknown endpoints require explicit approval in the operator terminal.

---

## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references: https://github.com/NVIDIA/NemoClaw, https://docs.nvidia.com/nemoclaw/latest/reference/inference-profiles.html, https://github.com/VoltAgent/awesome-nemoclaw, https://docs.ollama.com/integrations/nemoclaw -->

### Official Tools & Extensions

- **NVIDIA OpenShell** ([GitHub](https://github.com/NVIDIA/OpenShell)): The underlying secure runtime that NemoClaw builds upon. OpenShell is agent-framework-agnostic; NemoClaw is the OpenClaw-specific integration.
- **NVIDIA Nemotron models**: Local inference models purpose-built for agent tasks. Nemotron 3 Super (120B MoE) scored 85.6% on PinchBench for agentic tasks. Nemotron 3 Nano (4B) targets edge/consumer GPUs.
- **NVIDIA Endpoints** (`integrate.api.nvidia.com`): Cloud-hosted inference API for NVIDIA models.
- **Brev deployment** (experimental): Remote GPU instance deployment via `nemoclaw deploy`.
- **Telegram bridge**: `nemoclaw start` can launch a Telegram bot bridge for mobile agent access.
- **Cloudflared tunnel**: Built-in support for exposing sandboxed agents through Cloudflare tunnels.

### Community Ecosystem

- **[awesome-nemoclaw](https://github.com/VoltAgent/awesome-nemoclaw)**: Community-curated collection of presets, recipes, and playbooks for sandboxed OpenClaw operations.
- **[nemoclaw-installer](https://github.com/phioranex/nemoclaw-installer)**: Third-party one-liner installer for simplified setup.
- **[Ollama integration](https://docs.ollama.com/integrations/nemoclaw)**: Official Ollama documentation for NemoClaw local inference.
- **[build.nvidia.com/nemoclaw](https://build.nvidia.com/nemoclaw)**: NVIDIA's hosted playground for experimenting with NemoClaw configurations.
- **Discord community**: Active discussion at `discord.gg/XFpfPv9Uvx`.

### Common Integration Patterns

**Multi-provider inference setup:**
Configure multiple providers during onboarding and switch between them at runtime based on cost, latency, or privacy requirements:
```bash
# Switch to local Ollama for sensitive queries
openshell inference set --provider ollama --model nemotron-nano

# Switch to cloud for complex reasoning
openshell inference set --provider nvidia --model nemotron-super
```

**Preset-based network policy composition:**
Layer multiple presets to grant your agent access to the services it needs:
```bash
nemoclaw my-assistant policy-add   # Interactive: select slack, jira, pypi
# Or apply directly:
openshell policy set nemoclaw-blueprint/policies/presets/slack.yaml
openshell policy set nemoclaw-blueprint/policies/presets/jira.yaml
```

**CI/CD integration:**
Use `nemoclaw onboard` in a CI pipeline to create ephemeral sandboxed agents for code review, testing, or deployment tasks. Destroy after use with `nemoclaw <name> destroy`.

---

## Common Q&A
<!-- level: all -->

### Q: How does NemoClaw differ from just running OpenClaw in a Docker container?

Docker provides basic process and filesystem isolation, but it is not agent-aware. NemoClaw adds four critical layers on top: (1) deny-by-default network policies with operator approval workflows, (2) inference routing that keeps API credentials outside the container, (3) policy-aware request evaluation at the binary/destination/method/path level, and (4) cryptographically verified blueprints preventing supply-chain attacks. A Docker container does not know the difference between an HTTP request to download a package and one exfiltrating stolen credentials -- NemoClaw's policy engine does.

### Q: Can I use NemoClaw with agent frameworks other than OpenClaw?

Not directly. NemoClaw is tightly integrated with the OpenClaw CLI and plugin system. However, the underlying OpenShell runtime is more general-purpose. If your framework can run inside a container and communicate through a gateway, you could theoretically use OpenShell directly, but you would lose the one-command setup, blueprint lifecycle, and OpenClaw-specific integrations.

### Q: What happens if the agent needs access to a new endpoint that isn't in the policy?

The request is intercepted by the network namespace, blocked, and surfaced to the operator in the `openshell term` TUI. The operator can approve or deny the request in real time. Approved endpoints persist for the current session but do not modify the baseline policy. To permanently add an endpoint, edit `openclaw-sandbox.yaml` and re-run `nemoclaw onboard`.

### Q: How does the privacy router decide what goes to local vs. cloud inference?

The privacy router inspects query content and classifies data sensitivity. Queries containing PII, proprietary code, financial data, or other sensitive categories are routed to local Nemotron models. Non-sensitive queries can be routed to cheaper/faster cloud providers. The classification rules are configurable through policy.

### Q: What is the performance overhead of the sandbox and gateway?

Sandbox startup adds 30-60 seconds on first creation (image pull + resource provisioning); subsequent starts are faster. Gateway inference routing adds single-digit milliseconds of latency per request. The main overhead is resource consumption: the sandbox image is 2.4 GB compressed, and local inference models require their own VRAM allocation. For most use cases, the latency overhead is negligible compared to model inference time.

### Q: Can an agent inside the sandbox escalate privileges or escape isolation?

NemoClaw uses kernel-level enforcement (Landlock LSM for filesystem, seccomp for syscalls, network namespaces for networking). The gateway and agent run as distinct OS users. Config files are root-owned with SHA256 hash verification. Privilege escalation via `sudo`/`su` is blocked by seccomp profiles. This is fundamentally stronger than application-level sandboxing because the kernel enforces the rules regardless of what the application does. However, kernel exploits (while rare) would theoretically bypass these protections.

### Q: How do I handle the operational burden of approving network requests?

This is a real concern. Repetitive approval prompts can create "approval fatigue" and slow workflows. Best practices: (1) start with generous preset policies for known integrations (Slack, Jira, PyPI, etc.), (2) monitor the first few sessions to identify commonly needed endpoints, (3) add those endpoints to the baseline policy, (4) use dynamic policy updates for temporary access needs. Over time, the approval frequency should decrease significantly.

### Q: Is NemoClaw production-ready?

No. NemoClaw is alpha software released on March 16, 2026. The project explicitly states: "This software is not production-ready. Interfaces, APIs, and behavior may change without notice." Use it for evaluation, development, and testing. Wait for a stable release before deploying in production.

---

## Trade-offs & Limitations
<!-- level: intermediate -->
<!-- references: https://stormap.ai/post/inside-nemoclaw-the-architecture-sandbox-model-and-security-tradeoffs, https://repello.ai/blog/openclaw-vs-nemoclaw, https://dev.to/arshtechpro/nemoclaw-nvidias-open-source-stack-for-running-ai-agents-you-can-actually-trust-50gl, https://github.com/NVIDIA/NemoClaw -->

### Strengths

- **Kernel-level security enforcement.** Landlock, seccomp, and network namespaces are OS primitives that cannot be bypassed by application-layer exploits -- the correct abstraction level for containing autonomous agents.
- **Deny-by-default networking.** The most important design decision. Autonomous agents with unrestricted network access are a liability. NemoClaw inverts the default.
- **Credential isolation.** API keys never enter the sandbox. This single decision eliminates an entire class of credential-theft attacks.
- **Blueprint reproducibility.** Versioned, digest-verified blueprints eliminate "works on my machine" drift and prevent supply-chain tampering.
- **One-command setup.** Despite the underlying complexity (Docker, OpenShell, gateway, sandbox, policies, inference), the `curl | bash` installer abstracts it to a single command with a guided wizard.
- **Multi-provider inference flexibility.** Switch between NVIDIA, OpenAI, Anthropic, Gemini, and local Ollama at runtime without touching agent code.
- **Open source (Apache 2.0).** Full transparency and auditability of the security model.

### Limitations

- **Alpha stability.** APIs, CLI commands, and blueprint schemas will break between releases. Early adopters should expect migration pain.
- **Linux-first.** Full kernel-level isolation (Landlock, seccomp) is Linux-only. macOS and Windows support requires Docker Desktop, which reduces isolation guarantees and adds performance overhead.
- **OpenClaw lock-in.** NemoClaw is useless without OpenClaw. If the OpenClaw ecosystem stagnates or you switch agent frameworks, NemoClaw provides no value.
- **Resource requirements.** 4 vCPU, 8 GB RAM minimum, 2.4 GB sandbox image, plus model weights for local inference. Not suitable for constrained environments.
- **Operational complexity.** Despite the one-command installer, operators still manage Docker, OpenShell, YAML policies, blueprint versions, and credential files. The abstraction leaks when things go wrong.
- **Approval workflow friction.** Deny-by-default networking means the agent will be blocked frequently until policies are tuned. Approval fatigue is a real operational risk.
- **Local inference is experimental.** Ollama and vLLM support (especially on macOS) is marked experimental. OOM errors on machines under 8 GB RAM are common during setup.
- **No Windows/macOS kernel isolation.** The Docker Desktop path provides container isolation but not the Landlock/seccomp kernel hardening that makes the Linux path genuinely secure.

### Alternatives Comparison

| System | Focus | Relationship to NemoClaw |
|--------|-------|-------------------------|
| **OpenClaw (vanilla)** | Open-source AI agent platform | NemoClaw wraps and secures OpenClaw; it is not a replacement but a security layer |
| **OpenShell (standalone)** | General-purpose agent sandboxing runtime | NemoClaw's underlying runtime; can be used without NemoClaw for non-OpenClaw agents |
| **NanoClaw** | Lightweight agent orchestration | Targets teams that need agent orchestration without NVIDIA hardware requirements or OpenClaw's full-stack complexity |
| **DefenseClaw (Cisco)** | Agent security platform | Cisco's competing approach to agent security, announced after ClawHavoc |
| **Docker (plain)** | Container isolation | Provides basic isolation but lacks agent-aware policy, inference routing, and approval workflows |
| **gVisor / Firecracker** | Kernel-level sandboxing | Stronger isolation but no agent-specific features (inference routing, policy engine, blueprint lifecycle) |

### The Honest Take

NemoClaw solves a real and urgent problem: autonomous AI agents need containment, and the [ClawHavoc incident](https://cyberpress.org/clawhavoc-poisons-openclaws-clawhub-with-1184-malicious-skills/) proved that the OpenClaw ecosystem was not handling security adequately. The architecture is genuinely well-designed -- separating the plugin from the blueprint, enforcing security at the kernel level, and keeping credentials outside the sandbox are all correct decisions that reflect serious security engineering.

However, NemoClaw is alpha software backed by a single vendor (NVIDIA) with a vested interest in promoting its own hardware (Nemotron on DGX Spark, GeForce RTX) and cloud inference endpoints. The one-command installer is impressive for demos but hides substantial complexity. When something breaks -- and it will, because this is alpha -- operators need to understand Docker, OpenShell, network namespaces, YAML policies, and the blueprint lifecycle to debug it.

The biggest strategic risk is OpenClaw lock-in. NemoClaw's value is entirely dependent on OpenClaw remaining the dominant agent platform. If the market fragments (as it often does in fast-moving AI tooling), NemoClaw's tight coupling becomes a liability. OpenShell (the underlying runtime) is more portable, but NemoClaw's convenience features are all OpenClaw-specific.

For teams already committed to OpenClaw and handling sensitive data, NemoClaw is the most credible sandboxing solution available today. For everyone else, evaluate whether the operational complexity and platform lock-in are justified for your use case. And wait for a stable release before betting your production stack on it.
