# System Analysis: NemoClaw

## Metadata
- **Name:** NemoClaw
- **Category:** AI Agent Security & Infrastructure Runtime
- **Official URL:** https://www.nvidia.com/en-us/ai/nemoclaw/
- **GitHub:** https://github.com/NVIDIA/NemoClaw
- **Documentation:** https://docs.nvidia.com/nemoclaw/latest/index.html
- **License:** Apache 2.0
- **Latest Version:** Alpha / Early Preview (as of March 2026)
- **Analysis Date:** 2026-03-28

---

## Overview
<!-- level: beginner -->

NemoClaw is an open-source reference stack by NVIDIA that wraps OpenClaw -- the popular autonomous AI agent framework -- with enterprise-grade security, privacy, and infrastructure controls. Think of it as a **security jacket for AI agents**: the agent (OpenClaw) does the thinking, while NemoClaw ensures it can't go rogue, leak secrets, or reach systems it shouldn't touch.

Announced by Jensen Huang at GTC 2026 on March 16, 2026, NemoClaw addresses one of the biggest unsolved problems in the AI agent space: how do you let an autonomous agent operate continuously -- writing code, browsing the web, calling APIs -- without creating a massive security liability? NemoClaw's answer is **out-of-process policy enforcement**: security controls live outside the agent, at the operating system and network level, so the agent physically cannot override its own containment.

NemoClaw is currently in alpha and explicitly labeled as not production-ready by NVIDIA. However, it represents a genuine architectural advancement in agent security and has attracted significant enterprise interest, with partners including Adobe, SAP, Salesforce, and ServiceNow.

### What It Is

NemoClaw is a secure runtime wrapper for AI agents -- like a **bulletproof office** where an AI assistant works. The assistant can use the desk, the phone, and the filing cabinet (all pre-approved), but the walls, locks, and phone line restrictions are controlled by building security, not the assistant. Even if the assistant is tricked or compromised, it can't break through the physical containment.

### Who It's For

Enterprise teams and infrastructure engineers who want to deploy always-on AI agents (especially OpenClaw-based) with real security guarantees -- not just prompt-level "please don't do bad things" instructions. Also useful for security-conscious developers who want a sandboxed environment for agent experimentation without risking their host system.

### The One-Sentence Pitch

NemoClaw lets you run autonomous AI agents 24/7 with kernel-level security enforcement, privacy-preserving inference routing, and deny-by-default network policies -- so your agent can be productive without being dangerous.

---

## Core Concepts
<!-- level: beginner -->

### Claws (Agents)

A **Claw** is the OpenClaw term for an autonomous AI agent -- a program that can think, plan, and take actions on its own. Like a **new employee** at your company: capable and eager, but needs guardrails on what systems they can access on day one. NemoClaw doesn't change how claws work; it controls the environment they operate in.

### OpenShell (The Sandbox Runtime)

**OpenShell** is the sandboxed execution environment where agents run. Think of it as a **secure clean room**: everything the agent needs is inside (tools, files, network access to approved endpoints), but nothing unauthorized gets in or out. OpenShell is a standalone NVIDIA project that NemoClaw configures and orchestrates. Under the hood, it's a K3s Kubernetes cluster running inside a single Docker container with multiple isolation layers.

### Policies (The Rulebook)

**Policies** are declarative YAML files that define exactly what an agent can and cannot do -- which websites it can reach, which files it can write, which system calls it can make. Like **firewall rules for a single application**, but covering network, filesystem, and process behavior all at once. Policies follow a deny-by-default model: if it's not explicitly allowed, it's blocked.

### Gateway (The Security Guard)

The **Gateway** is the control-plane component that sits between the agent and the outside world. Every network request, every inference call, every credential use passes through the gateway. Like a **building security desk**: it checks every person (request) against the visitor list (policy), logs everything, and can stop suspicious activity in real time.

### Privacy Router (The Data Filter)

The **Privacy Router** inspects each inference query and classifies its sensitivity. Queries containing PII, proprietary code, or financial data get routed to local models (like Nemotron) and never leave your infrastructure. Non-sensitive queries can go to cloud models. Like a **mail room** that sorts letters: confidential mail goes by secure courier (local), regular mail goes by standard post (cloud).

### Blueprint (The Installation Plan)

A **Blueprint** is a versioned artifact containing the orchestration logic, default policies, and configuration for setting up NemoClaw. Like an **IKEA assembly manual** for your security infrastructure: it defines what components are needed, how they connect, and what the default settings should be. The blueprint follows a five-stage lifecycle: Resolve, Verify, Plan, Apply, Status.

### Inference Profile (The Model Router)

An **Inference Profile** defines which AI models handle which queries and where they run. It maps the agent's generic "I need a model" requests to specific providers (cloud APIs, local GPUs, or hybrid). Like a **phone switchboard**: the caller (agent) dials a single number, and the operator (profile) routes it to the right destination based on rules.

### How They Fit Together

An operator installs NemoClaw, which uses a **Blueprint** to set up an **OpenShell** sandbox. The sandbox runs **Claws** (agents) inside a secure container. Every action the claw takes is filtered through the **Gateway**, which enforces **Policies**. When the claw needs AI inference, the **Privacy Router** examines the request and the **Inference Profile** routes it to the appropriate model -- local or cloud. The operator monitors everything through the OpenShell terminal UI and can approve or deny network requests in real time.

---

## Architecture
<!-- level: intermediate -->

### High-Level Design

NemoClaw uses a **plugin-blueprint architecture** with two distinct layers:

1. **Plugin Layer (TypeScript)** -- A lightweight package that registers CLI commands (`nemoclaw onboard`, `nemoclaw list`, etc.) and the `/nemoclaw` slash command within OpenClaw. It handles blueprint resolution, version compatibility checks, and user interaction.

2. **Blueprint Layer (Python)** -- A versioned artifact (`nemoclaw-blueprint/`) containing orchestration logic, default policies, and configuration templates. It defines the `blueprint.yaml` for resource configuration and houses baseline policies.

Beneath both layers sits **OpenShell**, the actual runtime that does the heavy lifting of container isolation, policy enforcement, and inference routing.

### Key Components

**OpenShell Gateway** -- The central control plane. Exists because agents need a single, tamper-proof enforcement point. If security lived inside the agent process, a compromised agent could disable it. The gateway runs as a separate Linux user from the agent, preventing the agent from killing or modifying gateway processes.

**Sandbox Container** -- An isolated Docker container with restricted Linux capabilities. Exists because process-level isolation is the only reliable way to prevent an agent from accessing host resources. Uses Landlock LSM for filesystem restrictions and seccomp for syscall filtering.

**Policy Engine** -- Declarative YAML-based rules covering filesystem, network, process, and inference. Exists because hard-coded security is inflexible -- different deployments need different rules, and some rules (network, inference) need to be changeable at runtime without restarting the sandbox.

**Privacy Router** -- Inspects inference queries for sensitive content and routes accordingly. Exists because sending PII or proprietary code to cloud APIs creates compliance and legal risk. The router classifies data sensitivity and ensures sensitive queries stay on local infrastructure.

**K3s Cluster** -- A lightweight Kubernetes distribution running inside the Docker container. Exists because OpenShell needs container orchestration (managing gateway, sandbox, and policy engine as separate services) without requiring a full Kubernetes cluster on the host.

### Data Flow

Here's what happens when an agent tries to call an external API:

1. **Agent initiates request** -- The claw inside the sandbox makes an HTTP request (e.g., to `api.github.com`)
2. **DNS interception** -- The request hits `inference.local` (for model calls) or the sandbox's network stack
3. **Gateway intercept** -- OpenShell's gateway intercepts the outbound connection
4. **Policy check** -- The gateway looks up the destination host, port, requesting binary, and HTTP method against the YAML policy
5. **Decision**:
   - **Allowed**: Request passes through; credentials are injected by the gateway (never stored in the sandbox)
   - **Blocked**: Connection is denied and logged; if the operator has the TUI open, they see a real-time prompt to approve or deny
   - **Inference route**: Model calls are redirected through the Privacy Router, which classifies sensitivity and routes to local or cloud
6. **Response** -- The response flows back through the gateway to the agent

### Design Decisions

**Out-of-process enforcement over prompt-based guardrails** -- The most important architectural decision. Security constraints are enforced at the OS/network level, not by asking the model to behave. This means even a fully compromised agent (via prompt injection or malicious tool) is still contained by the sandbox.

**Deny-by-default networking** -- All outbound connections are blocked unless explicitly allowed in the policy YAML. This is the opposite of most development environments and is deliberately restrictive. The rationale: it's far safer to start locked down and selectively open access than to start open and try to block specific threats.

**Credential isolation** -- API keys are stored on the host in `~/.nemoclaw/credentials.json` (permissions `0600`) and injected by the gateway at request time. The agent never sees raw credentials. This prevents credential theft even if the sandbox is fully compromised.

**Two-user container model** -- The sandbox runs two distinct Linux users (gateway user and sandbox user). This prevents the agent from escalating privileges to modify the gateway process, even within its own container.

**Static + dynamic policy split** -- Filesystem and process policies are locked at container creation (can't be changed at runtime), while network and inference policies are hot-reloadable. This balances security (core isolation can't be weakened) with operational flexibility (network rules can adapt to new requirements).

---

## How It Works
<!-- level: intermediate -->

### Five-Layer Protection Model

NemoClaw's security is built on five distinct isolation layers, each enforced independently:

| Layer | Mechanism | When Applied | Can Agent Override? |
|-------|-----------|-------------|-------------------|
| **Container Isolation** | Docker containers with restricted capabilities | Locked at creation | No |
| **Process Hardening** | Dropped Linux capabilities, seccomp syscall filtering, `ulimit` (512 process max) | Locked at creation | No |
| **Filesystem Integrity** | Landlock LSM restricts writes to `/sandbox` and `/tmp` only; system directories read-only | Locked at creation | No |
| **Network Control** | Deny-by-default egress with YAML-defined allowlists per binary/endpoint | Hot-reloadable | No |
| **Inference Security** | All inference calls routed through gateway; credentials stored on host only | Hot-reloadable | No |

The key insight is that these layers are **independent**: even if one is somehow bypassed, the others remain intact. An agent that tricks its way past network policy still can't write to system files; an agent that finds a filesystem exploit still can't reach unapproved network endpoints.

### Filesystem Access Model

The Landlock Linux Security Module enforces strict filesystem boundaries:

- **Read-write**: `/sandbox` (working directory), `/tmp`, `/dev/null`
- **Read-only**: `/usr`, `/lib`, `/proc`, `/dev/urandom`, `/app`, `/etc`, `/var/log`
- **No access**: Everything else

This means the agent can do useful work (write code, create files, generate output) in its designated workspace, but cannot modify system binaries, tamper with configuration, or access the host filesystem.

### Network Policy Enforcement

Policies are defined in YAML with granular control over endpoints, allowed binaries, and HTTP methods:

```yaml
# Example: Allow GitHub API access only from the gh CLI
policies:
  github_rest_api:
    endpoints:
      - host: api.github.com
        port: 443
    allowed_binaries:
      - /usr/bin/gh
    methods:
      - GET
      - POST
      - PATCH
      - PUT
      - DELETE
```

The baseline policy (`openclaw-sandbox.yaml`) ships with 9 default policy groups covering Claude Code, NVIDIA APIs, GitHub, ClawHub, OpenClaw, npm registry, and Telegram.

### Real-Time Network Approval Flow

When an agent tries to reach an unlisted endpoint:

1. OpenShell intercepts and blocks the connection, logging the attempt
2. The TUI (`openshell term`) displays the blocked request with host, port, and requesting binary
3. The operator approves or denies in real time
4. Approved endpoints persist for the session only -- they are not saved to the baseline policy

This creates a "progressive trust" model where the operator starts with minimal access and selectively expands it as the agent demonstrates legitimate needs.

### Inference Routing

All model API calls from the sandbox are routed through a local DNS entry (`inference.local`) to the OpenShell gateway. The gateway then:

1. **Strips credentials** from the sandbox request (the agent never had them)
2. **Classifies data sensitivity** via the Privacy Router
3. **Routes to the appropriate provider** based on the inference profile:
   - Sensitive data (PII, proprietary code, financials) → local Nemotron models
   - Non-sensitive data → configured cloud provider (OpenAI, Anthropic, NVIDIA endpoints, etc.)
4. **Injects host-side credentials** for the selected provider
5. **Forwards the request** and returns the response to the sandbox

### Blueprint Lifecycle

The blueprint follows a five-stage lifecycle when `nemoclaw onboard` is run:

1. **Resolve** -- Validate the blueprint version against compatibility constraints
2. **Verify** -- Check the artifact digest (SHA256) to ensure integrity
3. **Plan** -- Determine what OpenShell resources need to be created or modified
4. **Apply** -- Execute the planned changes via the OpenShell CLI (create gateway, build sandbox image, create sandbox)
5. **Status** -- Report the current state of all components

### Performance Characteristics

Based on NVIDIA's published benchmarks (no independent verification yet):

- **PinchBench score**: 85.6% (highest among open models)
- **Token throughput**: 442 tokens/second
- **Context window**: Up to 1 million tokens
- **Inference throughput**: 2.2x more than GPT-OSS-120B; 7.5x more than Qwen3.5-122B (at 8k input / 16k output)
- **Sandbox image size**: ~2.4 GB compressed

**Caveat**: All performance numbers are from NVIDIA without independent third-party audits. The sandbox itself adds minimal overhead -- the main performance factor is which inference backend you use (local GPU vs. cloud API).

---

## Implementation Details
<!-- level: advanced -->

### Getting Started

**Prerequisites**: Linux (Ubuntu 22.04+), Docker 20.x+, Node.js 22.16+, npm 10+, 8 GB RAM minimum (16 GB recommended), 20 GB disk (40 GB recommended).

```bash
# Install NemoClaw
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash

# Run the interactive onboarding wizard
nemoclaw onboard
```

The `onboard` command walks through:
1. Creating the OpenShell gateway
2. Registering inference providers (enter API keys)
3. Building the sandbox image (~2.4 GB, takes a few minutes)
4. Creating your first sandbox
5. Applying the baseline network policy

```bash
# Connect to your sandbox
nemoclaw my-sandbox connect

# You're now inside the secured environment
# OpenClaw is pre-installed; start your agent
openclaw
```

### Configuration Essentials

| Config | Location | Purpose | When to Change |
|--------|----------|---------|---------------|
| **Credentials** | `~/.nemoclaw/credentials.json` | API keys for inference providers | When adding/rotating provider keys |
| **Sandbox metadata** | `~/.nemoclaw/sandboxes.json` | Sandbox names, defaults, model assignments | When managing multiple sandboxes |
| **Network policy** | `nemoclaw-blueprint/policies/openclaw-sandbox.yaml` | Allowed endpoints, binaries, methods | When agent needs new network access |
| **Policy presets** | `nemoclaw-blueprint/policies/presets/` | Pre-built rules for PyPI, Docker Hub, Slack, Jira | When enabling common integrations |
| **OpenShell state** | `~/.config/openshell/` | Gateway and cluster state | Rarely -- managed automatically |
| **Blueprint config** | `nemoclaw-blueprint/blueprint.yaml` | Resource definitions and orchestration | When customizing the deployment |

### CLI Reference

```bash
# Sandbox management
nemoclaw onboard                    # Interactive setup wizard
nemoclaw list                       # List all sandboxes with model/provider/policy info
nemoclaw <name> connect             # SSH into a sandbox
nemoclaw <name> status              # Show sandbox health and inference config
nemoclaw <name> logs [--follow]     # View or stream sandbox logs
nemoclaw <name> destroy             # Permanently delete a sandbox

# Policy management
nemoclaw <name> policy-add          # Add a policy preset to a sandbox
nemoclaw <name> policy-list         # List available and applied policy presets

# Auxiliary services
nemoclaw start                      # Start services (Telegram bridge, tunnel)
nemoclaw stop                       # Stop all auxiliary services
nemoclaw status                     # Show sandbox list and service status

# Advanced
nemoclaw deploy <instance-name>     # Deploy to remote GPU via Brev (experimental)
sudo nemoclaw setup-spark           # DGX Spark-specific setup (cgroup/Docker fixes)

# OpenShell direct commands
openshell term                      # Launch TUI for monitoring and egress approvals
openshell policy set <policy-file>  # Apply a policy to a running sandbox (session-only)
```

### Code Patterns

**Adding a custom network policy for a new API:**

```yaml
# my-custom-policy.yaml
policies:
  my_internal_api:
    endpoints:
      - host: api.internal.company.com
        port: 443
    allowed_binaries:
      - /usr/local/bin/claude
      - /usr/local/bin/openclaw
    methods:
      - GET
      - POST
```

```bash
# Apply statically (persists across restarts)
# Edit nemoclaw-blueprint/policies/openclaw-sandbox.yaml, then:
nemoclaw onboard

# Apply dynamically (session-only)
openshell policy set my-sandbox --policy my-custom-policy.yaml
```

**Configuring a local Ollama inference backend:**

```bash
# During onboard, select Ollama as a provider
# Or configure manually:
# 1. Ensure Ollama is running on the host
# 2. NemoClaw routes sandbox requests through gateway to host Ollama
# Note: On macOS, Ollama endpoint resolution may fail (known issue #385)
```

**Using the slash command inside OpenClaw:**

```
# Inside the sandbox, within an OpenClaw session:
/nemoclaw status    # Quick health check of sandbox, gateway, policies
```

### Deployment Considerations

- **Start with cloud inference** for evaluation -- local GPU setup adds significant complexity
- **Monitor with `openshell term`** during initial agent runs to see what network access the agent needs, then build your policy around observed behavior
- **The sandbox image is ~2.4 GB** -- on machines with <8 GB RAM, the build can trigger the OOM killer
- **K3s takes 1-3 minutes** to apply manifests after onboarding; health checks may time out with misleading namespace errors during this window
- **Do not use piped installs** (`curl | bash`) in automated environments -- they can skip critical prompts
- **Podman is not supported** -- NemoClaw requires Docker daemon-specific behaviors
- **For DGX Spark**: Run `sudo nemoclaw setup-spark` first to fix cgroup v2 and Docker issues on Ubuntu 24.04

---

## Use Cases & Case Studies
<!-- level: beginner-intermediate -->

### When to Use It

- **Always-on AI agents in enterprise environments** -- When you need an agent running 24/7 with real security guarantees, not just prompt-level restrictions. NemoClaw's kernel-level isolation is appropriate when agents access production systems, customer data, or internal APIs.

- **Compliance-sensitive deployments** -- When regulations require that certain data never leaves your infrastructure. The Privacy Router can keep PII and proprietary code on local models while routing non-sensitive queries to cloud providers.

- **Security-conscious agent experimentation** -- When you want to explore what autonomous agents can do without risking your host system. NemoClaw provides a sandboxed playground where a rogue or confused agent can't damage anything outside `/sandbox`.

- **Multi-model inference routing** -- When you want to use the best model for each task (local Nemotron for private data, cloud GPT/Claude for general tasks) with automatic routing based on data sensitivity.

- **Teams evaluating agent security architectures** -- NemoClaw's open-source, well-documented security model serves as a reference implementation for how agent sandboxing should work, even if you ultimately build your own.

### When NOT to Use It

- **Production workloads today** -- NemoClaw is alpha software. NVIDIA explicitly warns it is not production-ready. Wait for at least beta stability (analysts suggest evaluating for production in Q3 2026 at earliest).

- **macOS or Windows as primary platform** -- NemoClaw is Linux-first. macOS (Apple Silicon via Colima/Docker Desktop) has partial support with known issues. WSL2 support is experimental with significant manual intervention required. Intel Macs are unsupported entirely.

- **Low-resource environments** -- Minimum 8 GB RAM and 20 GB disk just for the sandbox infrastructure. If you're running on a lightweight VM or Raspberry Pi, NemoClaw's overhead is too high.

- **Simple, supervised agent tasks** -- If your agent runs a single task under human supervision and doesn't access sensitive systems, NemoClaw's security infrastructure is overkill. Just use OpenClaw directly.

- **Multi-tenant isolation** -- NemoClaw operates at single-sandbox level. It is not designed for hostile multi-tenant isolation where different users' agents must be isolated from each other.

### Real-World Examples

**GTC 2026 "Build-a-Claw" Event** -- NVIDIA demonstrated NemoClaw at GTC 2026 with live sandbox creation and agent deployment, showcasing the onboarding wizard and real-time network approval flow for a coding agent.

**Enterprise Partner Evaluations** -- Adobe, SAP, Salesforce, and ServiceNow are launch partners evaluating NemoClaw for securing their AI agent deployments. These are assessment-phase engagements, not production deployments (as of March 2026).

**Community Deployment Guides** -- The community has published deployment guides for running NemoClaw on DigitalOcean Droplets, DGX Spark, and via NVIDIA Brev for remote GPU access, indicating active experimentation across different infrastructure setups.

---

## Ecosystem & Integrations
<!-- level: intermediate -->

### Official Tools & Extensions

- **OpenShell** -- The standalone sandbox runtime that NemoClaw orchestrates. Can be used independently of NemoClaw for other agents (Claude Code, Codex, GitHub Copilot).
- **Nemotron Models** -- NVIDIA's open model family for local inference. Nemotron 3 Super 120B MoE (flagship) and Nemotron 3 Nano 4B (edge).
- **AI-Q Blueprint** -- NVIDIA's development accelerator for agents, ranked top of DeepResearch Bench.
- **NVIDIA NIM** -- Local inference serving for NVIDIA models (experimental integration with NemoClaw).

### Community Ecosystem

- **awesome-nemoclaw** (GitHub: VoltAgent/awesome-nemoclaw) -- Community-curated collection of resources, tutorials, and tools.
- **DeepWiki** -- Auto-generated codebase documentation for the NemoClaw repository.
- **Community deployment guides** -- Tutorials on Medium, DEV Community, DigitalOcean, and Substack.
- **Policy presets** -- Community-contributed YAML policies for common services (PyPI, Docker Hub, Slack, Jira).

### Common Integration Patterns

**NemoClaw + OpenClaw** -- The primary integration. NemoClaw wraps OpenClaw with security controls. OpenClaw provides the agent framework; NemoClaw provides the secure runtime.

**NemoClaw + Local GPU (Nemotron/Ollama/vLLM)** -- For privacy-sensitive workloads. Run models locally on RTX/DGX hardware, with NemoClaw routing sensitive queries to local inference and general queries to cloud APIs.

**NemoClaw + Cloud APIs (Anthropic/OpenAI/NVIDIA Endpoints)** -- For compute-flexible deployments. NemoClaw manages credential isolation and policy enforcement while using cloud models for inference.

**NemoClaw + LangChain** -- NVIDIA has announced LangChain integration for building agent workflows that run inside NemoClaw sandboxes.

**NemoClaw + Enterprise Security Stack** -- Partnerships with Cisco, CrowdStrike, Google Cloud, Microsoft Security, and TrendAI for runtime policy management alignment.

---

## Common Q&A
<!-- level: all -->

### Q: What happens if the agent is prompt-injected inside the NemoClaw sandbox?

The agent may still process the malicious prompt -- NemoClaw does not include prompt injection detection or content safety scanning. However, the **blast radius is dramatically reduced**: the agent can only write to `/sandbox` and `/tmp`, can only reach pre-approved network endpoints, and never has access to raw API credentials. A prompt-injected agent inside NemoClaw is like a burglar locked in an empty room -- they can make a mess, but they can't reach anything valuable.

### Q: Can NemoClaw prevent an agent from exfiltrating data through approved endpoints?

Not directly. If an agent is allowed to reach `api.github.com`, it could theoretically push sensitive data to a repo. NemoClaw controls **which** endpoints are reachable and **which HTTP methods** are allowed, but it does not inspect the content of allowed requests. For data exfiltration prevention, you would need to layer additional controls (DLP tooling, network inspection) on top of NemoClaw's policies. The deny-by-default model helps by minimizing the set of possible exfiltration targets.

### Q: How does NemoClaw compare to just running agents in Docker containers?

Docker provides process isolation but not the agent-specific controls NemoClaw adds: deny-by-default networking with per-binary rules, inference routing with credential isolation, Landlock filesystem restrictions, real-time egress approval UI, and the Privacy Router for sensitive data classification. Plain Docker gives you walls; NemoClaw gives you walls plus a security guard, a mail filter, and a visitor log.

### Q: What are the practical scaling limits of NemoClaw?

NemoClaw currently operates in "single-player mode" -- one sandbox per gateway, one trusted operator per gateway. There is no multi-tenant isolation, no horizontal scaling of sandboxes, and no centralized management of multiple NemoClaw instances. For teams needing dozens of sandboxed agents, you would need to run separate NemoClaw instances, each with its own gateway and policy configuration. NVIDIA has indicated multi-tenant support is on the roadmap but has not committed to a timeline.

### Q: If NemoClaw is alpha, what security vulnerabilities have been found?

At least two CVEs have been disclosed: CVE-2026-24763 (Docker sandbox command injection) and CVE-2026-22179 (shell parsing bypass). These are classical container escape vectors, not fundamental design flaws. The out-of-process enforcement model is architecturally sound, but the implementation is young and will likely have more vulnerabilities discovered as it matures. This is a key reason NVIDIA labels it as not production-ready.

### Q: Can I use NemoClaw with models other than NVIDIA's Nemotron?

Yes. NemoClaw supports multiple inference backends: Anthropic (Claude), OpenAI, Google Gemini, Ollama (local), vLLM (local, experimental), NVIDIA NIM (local, experimental), and any OpenAI-compatible or Anthropic-compatible endpoint. The Privacy Router and credential isolation work regardless of which provider you use. Nemotron is the recommended choice for local inference on NVIDIA hardware, but it's not required.

### Q: How do I debug network issues inside the sandbox?

Use `openshell term` to launch the TUI, which shows all blocked network requests in real time with the requesting binary, destination host, and port. For deeper debugging, `nemoclaw <name> logs --follow` streams sandbox logs, and the sandbox includes standard networking tools (`ping`, `dig`, `nslookup`, `nc`, `traceroute`, `netstat`). The most common issue is a legitimate request being blocked by the deny-by-default policy -- approve it in the TUI or add it to the YAML policy.

### Q: What's the relationship between NemoClaw, OpenClaw, and OpenShell?

**OpenClaw** is the autonomous AI agent framework (the "brain"). **OpenShell** is the sandboxed runtime environment (the "secure room"). **NemoClaw** is the orchestration layer that configures OpenShell specifically for OpenClaw agents, adding default policies, the onboarding wizard, CLI commands, and the blueprint lifecycle. You can use OpenShell without NemoClaw (for other agents like Claude Code or Codex), and you can use OpenClaw without NemoClaw (without security controls). NemoClaw is the opinionated combination of both.

---

## Trade-offs & Limitations
<!-- level: intermediate -->

### Strengths

- **Out-of-process enforcement** -- The most significant technical strength. Security lives at the OS/network level, not inside the agent. This is a genuinely better architecture than prompt-level or application-layer guardrails for autonomous agents.

- **Deny-by-default networking with per-binary granularity** -- Not just "allow/block this host" but "allow this binary to reach this host with these HTTP methods." Combined with real-time approval UI, this is more granular than most container networking solutions.

- **Credential isolation** -- API keys never enter the sandbox. The gateway injects credentials at request time. Even a fully compromised sandbox cannot steal provider credentials.

- **Privacy Router** -- Automatic classification and routing of sensitive data to local models is a meaningful enterprise feature that addresses real compliance requirements.

- **Open source (Apache 2.0)** -- Full transparency into the security model. The community can audit, extend, and contribute. No vendor lock-in on the core security infrastructure.

### Limitations

- **Alpha maturity** -- Not production-ready by NVIDIA's own admission. Known CVEs, incomplete platform support, missing features. Plan for Q3 2026 evaluation at earliest for production use.

- **Linux-only (practically)** -- macOS has partial support with known bugs (Ollama routing, `/etc/hosts` issues). WSL2 is experimental. Intel Macs are unsupported. This severely limits developer adoption for those not on Linux workstations.

- **No multi-tenant isolation** -- Single-sandbox, single-operator model. Cannot isolate agents from each other within a shared NemoClaw instance. Enterprise teams with multiple agents need separate instances.

- **No content-level security** -- NemoClaw controls what the agent can *reach* but not what it *says or sends*. No PII scanning of agent outputs, no prompt injection detection, no content safety filtering. These must be layered separately.

- **No granular tool governance** -- Cannot allow/block/rate-limit specific tool calls within the agent. If the agent has access to a tool, it can use it without restriction within the sandbox's filesystem and network boundaries.

- **Complex setup and resource overhead** -- Requires Docker, K3s, 8+ GB RAM, 20+ GB disk just for the infrastructure. The onboarding wizard helps, but the underlying complexity surfaces quickly when things go wrong.

- **Performance concerns** -- Local inference with Nemotron is slower than expected according to early reviews. No independent benchmarks to validate NVIDIA's published numbers.

### Alternatives Comparison

**Plain Docker / Docker-in-Docker** -- Simpler to set up and more widely understood. Provides process isolation but lacks agent-specific controls (per-binary network policies, inference routing, credential isolation, real-time approval). Choose Docker when you need basic isolation without agent-aware security. Choose NemoClaw when you need the full agent security stack.

**E2B (Code Interpreter SDK)** -- Cloud-hosted sandboxes for AI code execution. Easier to get started, no local infrastructure needed, better multi-tenant support. But less control over the security model, data leaves your infrastructure, and you depend on E2B's availability. Choose E2B for quick prototyping with cloud sandboxes. Choose NemoClaw for on-premise, privacy-sensitive deployments.

**Firecracker / gVisor** -- Lower-level VM/sandbox technologies with stronger isolation guarantees. More mature and battle-tested but require significant engineering to build agent-specific tooling on top. Choose these when you need maximum isolation and are willing to build the agent orchestration yourself. Choose NemoClaw when you want a pre-built agent security stack.

### The Honest Take

NemoClaw's architecture is genuinely innovative -- out-of-process enforcement for AI agents is the right approach, and the deny-by-default networking with per-binary granularity is more thoughtful than anything else in the open-source agent security space. But it's alpha software that shows it. The setup is complex, the platform support is narrow, and critical features (multi-tenant, content security, tool governance) are missing. Use it today for experimentation, security research, and architecture evaluation. Wait for beta before planning production deployments. If you're on macOS or Windows, wait longer.
