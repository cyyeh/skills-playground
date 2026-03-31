## Architecture
<!-- level: intermediate -->
<!-- references:
- [NemoClaw Architecture Reference](https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html) | official-docs
- [How NemoClaw Works](https://docs.nvidia.com/nemoclaw/latest/about/how-it-works.html) | official-docs
- [NemoClaw GitHub Repository](https://github.com/NVIDIA/NemoClaw) | github
-->

### High-Level Design

NemoClaw's architecture is a two-layer system with a clear separation of concerns: a thin TypeScript plugin handles the user-facing CLI and orchestration logic, while a Python blueprint runtime handles the actual provisioning and management of sandboxed environments. Both layers communicate through the [OpenShell](https://docs.nvidia.com/nemoclaw/latest/about/overview.html) runtime, which provides the kernel-level primitives for isolation and network control.

The overall design follows a "wrapping" philosophy rather than a "forking" one. Instead of modifying OpenClaw's source code to add security, NemoClaw places an unmodified OpenClaw installation inside a controlled container and governs it from the outside -- like surrounding an existing building with a security perimeter rather than renovating its interior.

### Key Components

**NemoClaw CLI (`bin/nemoclaw.js`)** -- The user's primary interface. It handles onboarding, sandbox lifecycle management (create, connect, destroy, status, logs), and policy operations. This component exists because operators need a single entry point to manage the entire stack without manually orchestrating Docker, OpenShell, and OpenClaw separately.

**TypeScript Plugin (`nemoclaw/src/`)** -- Runs in-process within the OpenClaw gateway sandbox. It manages blueprint resolution, state tracking, credential stripping, and digest verification. This layer exists because the system needs a trusted component that can operate inside the gateway context while enforcing security invariants that the agent itself cannot bypass.

**Python Blueprint (`nemoclaw-blueprint/`)** -- A versioned artifact containing the manifest (`blueprint.yaml`) and policies (`openclaw-sandbox.yaml`). The blueprint is the declarative specification of a deployment. It exists as a separate artifact with its own release stream so that sandbox configurations can be versioned, audited, and rolled back independently of the CLI or plugin code.

**OpenShell Gateway** -- The NVIDIA-provided runtime that intercepts all traffic between the sandbox and the outside world. It enforces network policies, routes inference requests to configured providers, and provides the TUI for operator monitoring. This is the security backbone -- without it, the sandbox would need to implement its own network interception and policy enforcement from scratch.

**Sandbox Container (`ghcr.io/nvidia/openshell-community/sandboxes/openclaw`)** -- A pre-built Docker image containing OpenClaw and the NemoClaw plugin, hardened with capability drops and least-privilege rules. The container exists to provide a reproducible, tamper-evident environment where the agent operates. Its [Dockerfile](https://github.com/NVIDIA/NemoClaw) follows a security-first design with explicit capability drops.

**Messaging Bridges (`scripts/telegram-bridge.js`)** -- Optional connectors that link external messaging platforms (Telegram, Discord, Slack) to the sandboxed agent. These exist so that always-on assistants can be reached through channels teams already use, without requiring direct access to the sandbox host.

### Data Flow

A typical interaction follows this path through the system:

1. **User sends a message** via the OpenClaw TUI, CLI, or a messaging bridge (e.g., Telegram).
2. **The message enters the sandbox** through the OpenShell gateway, which validates the incoming connection.
3. **OpenClaw processes the message** inside the sandbox, deciding whether to respond directly or execute a tool (file read, shell command, etc.).
4. **If the agent needs LLM inference**, it calls `inference.local` -- a local endpoint inside the sandbox that does not hold any real API credentials.
5. **OpenShell intercepts the inference request** at the sandbox boundary, injects the real API credentials stored on the host, and forwards the request to the configured inference provider (NVIDIA Endpoints, OpenAI, Anthropic, local Ollama, etc.).
6. **If the agent attempts a network request** to a domain not in the network policy, OpenShell blocks the request and surfaces it in the operator TUI for approval.
7. **The inference response returns** through the same controlled path: provider to OpenShell gateway to sandbox to agent.
8. **The agent's response** is delivered back to the user through the same channel that originated the request.

### Design Decisions

**Wrapping over forking** -- NemoClaw runs an unmodified OpenClaw inside a sandbox rather than maintaining a security-hardened fork. This decision trades some depth of integration for maintainability: NemoClaw can absorb upstream OpenClaw updates without merge conflicts, and the security boundary is enforced externally rather than relying on in-application checks that could be bypassed.

**Deny-by-default networking** -- Every outbound connection is blocked unless explicitly allowed in the network policy YAML. This is the opposite of most development environments, which default to open. The rationale is that autonomous agents executing arbitrary code present a fundamentally different threat model than human developers -- an agent that autonomously discovers a useful API and starts calling it is exactly the scenario NemoClaw is designed to prevent without human approval.

**Host-side credential management** -- API keys never enter the sandbox. The agent sees only `inference.local` as its model endpoint, while OpenShell on the host holds the real credentials and injects them into forwarded requests. This architectural decision means that even a fully compromised sandbox (e.g., through a prompt injection attack that achieves code execution) cannot exfiltrate API keys.

**Blueprint versioning with digest verification** -- Blueprints are versioned artifacts whose integrity is checked via content digests before application. This ensures that the sandbox configuration a security team approved is exactly the configuration that gets deployed, with no possibility of silent modification.

**Two-language split (TypeScript + Python)** -- The CLI and plugin are TypeScript (because they integrate with the Node.js-based OpenClaw ecosystem), while the blueprint runtime is Python (because it interacts with OpenShell's Python-based tooling). This split creates some complexity but avoids forcing either ecosystem to use a non-native language for its integration points.
