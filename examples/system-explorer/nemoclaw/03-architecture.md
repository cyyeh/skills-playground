## Architecture
<!-- level: intermediate -->
<!-- references:
- [NemoClaw Architecture Reference](https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html) | official-docs
- [How NemoClaw Works](https://docs.nvidia.com/nemoclaw/latest/about/how-it-works.html) | official-docs
- [NemoClaw GitHub - Repository Structure](https://github.com/NVIDIA/NemoClaw) | github
-->

NemoClaw is a two-tier system layered atop NVIDIA OpenShell. The architecture follows a deliberate separation of concerns: a lightweight TypeScript plugin handles user interaction and CLI wiring, while a versioned Python blueprint manages all orchestration logic for sandbox creation, policy enforcement, and inference routing.

### High-Level Architecture

The system consists of four main layers, each with a distinct responsibility:

**1. CLI Layer (TypeScript Plugin)**
The plugin (`nemoclaw/src/`) registers commands under `openclaw nemoclaw` using Commander.js. It contains the entry point (`index.ts`), CLI wiring (`cli.ts`), and command modules for launch, connect, status, logs, and slash-command handling. This layer runs in-process with the OpenClaw gateway and is intentionally kept thin — its job is to accept user input, resolve the correct blueprint version, and delegate orchestration to the blueprint subprocess.

**2. Orchestration Layer (Python Blueprint)**
The blueprint (`nemoclaw-blueprint/`) is a versioned artifact containing the Dockerfile, security policies, network rules, and Python orchestration logic. It follows a five-stage lifecycle: resolve (locate and validate the artifact), verify (check the digest), plan (determine required OpenShell resources), apply (execute the plan via OpenShell CLI), and status (report deployment state). The blueprint is immutable once published — any changes require a new version with a new digest.

**3. Security Layer (OpenShell Runtime)**
NVIDIA OpenShell provides the foundational security primitives. It creates and manages sandbox containers, enforces Landlock filesystem policies, applies seccomp BPF syscall filters, configures network namespaces for egress control, and hosts the inference routing gateway. OpenShell operates entirely outside the agent's reach — the agent cannot modify, disable, or bypass its controls.

**4. Agent Layer (OpenClaw)**
The OpenClaw agent runs inside the sandbox container. It sees a standard Linux environment with `/sandbox` and `/tmp` as writable directories, a local inference endpoint at `inference.local`, and network access limited to policy-approved endpoints. From the agent's perspective, it operates normally — the security controls are transparent and cannot be detected or circumvented.

### Component Interactions

The components interact through a clear chain of command:

- **User → Plugin:** The operator runs `nemoclaw onboard`, `nemoclaw connect`, or other CLI commands.
- **Plugin → Blueprint:** The plugin downloads the blueprint artifact, verifies its digest, and executes it as a subprocess.
- **Blueprint → OpenShell:** The blueprint calls `openshell sandbox create`, `openshell provider add`, and `openshell policy apply` to configure the runtime.
- **OpenShell → Sandbox:** OpenShell creates the isolated container, applies security policies, and starts the agent process.
- **Agent → OpenShell Gateway:** All inference requests from the agent go through `inference.local`, which OpenShell routes to the configured provider.
- **Agent → Network Policy:** All outbound connections are intercepted by the network namespace. Unapproved destinations are blocked and surfaced to the operator.

### Repository Structure

The codebase is organized into five main directories:

- `bin/` — CLI entry point (CommonJS wrapper)
- `nemoclaw/` — TypeScript plugin source (Commander CLI extension)
- `nemoclaw-blueprint/` — Blueprint YAML, policies, Dockerfile, and Python orchestration
- `scripts/` — Installation, uninstallation, and automation helpers
- `test/` — Integration and end-to-end tests
- `docs/` — Sphinx/MyST documentation source

### Host-Side State

NemoClaw stores configuration and metadata on the host filesystem:

- `~/.nemoclaw/credentials.json` — Provider API keys (never copied into the sandbox)
- `~/.nemoclaw/sandboxes.json` — Sandbox metadata and version tracking
- `~/.openclaw/openclaw.json` — OpenClaw configuration snapshots

### Design Principles

The architecture adheres to five core tenets:

1. **Thin plugin, versioned blueprint** — The plugin stays stable; orchestration logic evolves in the blueprint.
2. **CLI boundary respect** — The `nemoclaw` CLI is the primary management interface; no hidden background processes.
3. **Supply chain safety** — Blueprint artifacts are immutable, versioned, and digest-verified before execution.
4. **OpenShell-native** — New installations use `openshell sandbox create` directly, not plugin-driven bootstrapping.
5. **Reproducible setup** — Re-running setup recreates the sandbox from identical blueprint and policy definitions.
