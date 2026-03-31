## Architecture
<!-- level: intermediate -->
<!-- references:
- [NemoClaw Architecture Reference](https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html) | official-docs
- [NemoClaw GitHub](https://github.com/NVIDIA/NemoClaw) | github
- [NemoClaw Architecture Deep Dive](https://particula.tech/blog/nvidia-nemoclaw-openclaw-enterprise-security) | article
- [How NemoClaw Actually Works](https://www.yottalabs.ai/post/how-nemoclaw-actually-works-architecture-scaling-and-deployment-explained) | article
-->

NemoClaw's architecture follows a defense-in-depth model with four distinct layers, each providing independent security guarantees. The key architectural insight is that policy enforcement happens *outside* the agent's address space — a compromised agent cannot modify its own constraints.

### High-Level Component Diagram

```
+------------------------------------------------------------------+
|  USER INTERFACES                                                  |
|  [Terminal TUI]  [Telegram]  [Discord]  [Slack]  [CLI]          |
+------------------------------------------------------------------+
        |                                                           
        v                                                           
+------------------------------------------------------------------+
|  NEMOCLAW CLI (TypeScript Plugin Layer)                          |
|  +-----------+ +-----------+ +-----------+ +-----------+        |
|  | launch    | | connect   | | status    | | logs      |        |
|  +-----------+ +-----------+ +-----------+ +-----------+        |
|  +--------------------+ +--------------------+                   |
|  | Blueprint Resolver | | Digest Verifier    |                   |
|  +--------------------+ +--------------------+                   |
|  +--------------------+                                          |
|  | State Manager      |                                          |
|  +--------------------+                                          |
+------------------------------------------------------------------+
        |                                                           
        v                                                           
+------------------------------------------------------------------+
|  BLUEPRINT LAYER (Python Orchestration)                          |
|  +-----------------------------------------------------------+  |
|  | blueprint.yaml  — version constraints & manifest          |  |
|  | openclaw-sandbox.yaml  — network & filesystem policies    |  |
|  | Blueprint Runner — Plan → Apply → Status lifecycle        |  |
|  +-----------------------------------------------------------+  |
+------------------------------------------------------------------+
        |                                                           
        v                                                           
+==================================================================+
||  OPENSHELL RUNTIME (Kernel-Level Enforcement)                  ||
||                                                                 ||
||  +-----------------------------------------------------------+ ||
||  |  SANDBOX CONTAINER                                        | ||
||  |  +-----------------------------------------------------+ | ||
||  |  |  OPENCLAW AGENT                                      | | ||
||  |  |  +----------+ +----------+ +----------+             | | ||
||  |  |  | Planner  | | Executor | | Tools    |             | | ||
||  |  |  +----------+ +----------+ +----------+             | | ||
||  |  |  +----------+ +----------+                          | | ||
||  |  |  | Memory   | | NemoClaw |                          | | ||
||  |  |  |          | | Plugin   |                          | | ||
||  |  |  +----------+ +----------+                          | | ||
||  |  +-----------------------------------------------------+ | ||
||  +-----------------------------------------------------------+ ||
||                                                                 ||
||  +-----------------------------------------------------------+ ||
||  |  POLICY ENGINE (Rust)                                     | ||
||  |  [Network Policy] [Filesystem Policy] [Process Limits]    | ||
||  +-----------------------------------------------------------+ ||
||                                                                 ||
||  +-----------------------------------------------------------+ ||
||  |  KERNEL SECURITY                                          | ||
||  |  [Landlock] [seccomp] [Network Namespaces] [Cap Drop]    | ||
||  +-----------------------------------------------------------+ ||
+==================================================================+
        |                                                           
        v                                                           
+------------------------------------------------------------------+
|  INFERENCE LAYER                                                  |
|  +--------------------+    +-------------------+                 |
|  | Privacy Router     | -> | Local Nemotron    |                 |
|  | (Sensitivity       |    | (On-Premises)     |                 |
|  |  Classification)   |    +-------------------+                 |
|  +--------------------+    +-------------------+                 |
|          |              -> | Cloud Providers   |                 |
|          |                 | (OpenAI, etc.)    |                 |
|          |                 +-------------------+                 |
|          v                                                       |
|  +--------------------+                                          |
|  | Credential         |                                          |
|  | Injection Gateway  |                                          |
|  +--------------------+                                          |
+------------------------------------------------------------------+
        |                                                           
        v                                                           
+------------------------------------------------------------------+
|  HOST-SIDE STATE                                                  |
|  ~/.nemoclaw/credentials.json  — Provider API keys              |
|  ~/.nemoclaw/sandboxes.json    — Sandbox registry               |
|  Audit logs  — Kernel-level action recording                    |
+------------------------------------------------------------------+
```

### Layer 1: TypeScript Plugin Layer

The plugin layer is a TypeScript Commander CLI extension that integrates with the OpenClaw CLI. It handles:

- **Command registration:** Exposes `launch`, `connect`, `status`, and `logs` commands
- **Blueprint resolution:** Locates and downloads blueprint artifacts from OCI registries with local caching
- **Digest verification:** Ensures artifact integrity before deployment
- **Subprocess execution:** Invokes the Python blueprint runner as a child process
- **State management:** Persists sandbox configurations in `~/.nemoclaw/sandboxes.json`

The plugin also provides the `/nemoclaw` slash command within the agent's chat interface, giving operators real-time control over sandbox behavior.

### Layer 2: Python Blueprint Layer

The blueprint is a versioned artifact that declaratively defines the sandbox environment. It contains:

- **`blueprint.yaml`:** Version constraints and the deployment manifest
- **`openclaw-sandbox.yaml`:** Network egress rules, filesystem mount policies, and process restrictions
- **Blueprint Runner:** A TypeScript runtime that executes a five-stage lifecycle:
  1. **Resolve** — Locate the blueprint artifact and check version compatibility
  2. **Verify** — Validate the OCI digest for tamper detection
  3. **Plan** — Calculate the diff between current and desired sandbox state
  4. **Apply** — Execute OpenShell CLI commands to create or update resources
  5. **Status** — Report the sandbox's current configuration and health

### Layer 3: OpenShell Runtime (The Security Boundary)

This is the most critical layer — the point where NemoClaw diverges from permissive agent frameworks. OpenShell provides:

**Out-of-Process Policy Engine:** A Rust-based service running in a separate process from the agent. It intercepts system calls and network requests at the kernel boundary. Because the engine runs outside the agent's address space, a compromised agent cannot tamper with its own restrictions.

**Kernel Security Primitives:**
- **Landlock:** Linux security module for fine-grained filesystem access control. The sandbox can only read and write to `/sandbox` and `/tmp`; system paths are read-only.
- **seccomp:** Syscall filtering that restricts which kernel functions the sandbox process can invoke, blocking dangerous operations like raw socket creation or kernel module loading.
- **Network namespaces:** Complete network isolation. The sandbox has its own network stack with no default routes. All traffic must go through the OpenShell gateway.
- **Capability dropping:** The container runs with minimal Linux capabilities, preventing privilege escalation.

**Network Policy Enforcement:** Every outbound connection is validated against the YAML policy. Unknown destinations are blocked by default. When an agent attempts to reach an unapproved endpoint, the request is surfaced in the operator's TUI for real-time approval or denial.

### Layer 4: Inference Layer

The inference layer manages all LLM communication:

**Privacy Router:** Classifies each inference request by data sensitivity using organization-defined rules. Sensitive requests (containing PII, proprietary code, financial data) are routed to local Nemotron models. Non-sensitive requests can go to cloud providers.

**Credential Injection Gateway:** The sandbox never holds API credentials. The gateway intercepts outgoing inference requests and injects the appropriate authentication tokens based on the configured provider. Supported providers:
- **NVIDIA Endpoints** (default) — `nvidia/nemotron-3-super-120b-a12b`
- **Local Ollama** — for air-gapped environments
- **Custom providers** — any OpenAI-compatible API endpoint

### Data Flow

A typical request traverses the stack as follows:

1. User sends a message via terminal, Telegram, or other channel
2. The message bridge (SSH-based, avoiding direct network exposure for the agent) delivers it into the sandbox
3. OpenClaw's planner evaluates the request and determines if tools are needed
4. If tools are required, the agent invokes registered tools within the sandbox
5. If external network access is needed, the Network Policy Engine evaluates the request
6. If inference is needed, the Privacy Router classifies sensitivity and selects a provider
7. The Inference Gateway proxies the request with injected credentials
8. The response flows back through the same path, with every step logged in the audit trail
9. The final response is delivered to the user via the same messaging channel

### Security Architecture Principles

**Defense in Depth:** Multiple independent security layers ensure that no single failure compromises the system. Even if the agent bypasses one control, others remain active.

**Least Privilege:** The sandbox starts with no capabilities and adds only what is explicitly needed. Network, filesystem, and process access must be granted by policy.

**Out-of-Process Enforcement:** Security policies are enforced by a separate process (the Rust policy engine) at the kernel level. This architectural separation is the key innovation — prompt-level guardrails can be bypassed through injection; kernel-level policies cannot.

**Credential Isolation:** API keys, tokens, and authentication secrets live on the host, not in the sandbox. The gateway injects them at the boundary, so a sandbox compromise cannot leak credentials.
