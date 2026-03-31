## Architecture
<!-- level: intermediate -->
<!-- references:
- [NemoClaw Architecture Reference](https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html) | official-docs
- [NemoClaw GitHub Repository](https://github.com/NVIDIA/NemoClaw) | github
- [OpenShell Technical Blog](https://developer.nvidia.com/blog/run-autonomous-self-evolving-agents-more-safely-with-nvidia-openshell/) | blog
- [NemoClaw Architecture on GitHub](https://github.com/NVIDIA/NemoClaw/blob/main/docs/reference/architecture.md) | github
-->

### System Overview

NemoClaw is architected as a two-component system built on top of NVIDIA OpenShell, spanning three operational levels: the host machine, the OpenShell runtime, and the sandboxed container. This separation is intentional -- it ensures that security-critical components (policy enforcement, credential storage, inference routing) live outside the agent's execution environment where they cannot be tampered with.

The design philosophy is "out-of-process policy enforcement." Rather than embedding guardrails within the agent (which can be circumvented), constraints are enforced at the runtime environment level. This is comparable to browser tab isolation: a malicious web page can't read your passwords because the browser sandbox prevents it at the process level, not because the page chooses not to.

### The Two Core Components

**TypeScript Plugin (CLI):** A thin Commander.js-based package that registers the `nemoclaw` CLI command and an inference provider. It runs in-process with the OpenClaw gateway inside the sandbox. The plugin handles command registration, blueprint resolution and verification, persistent state tracking, SSRF validation for network requests, and migration snapshots with credential stripping.

The plugin is intentionally kept minimal and stable. Its job is user interaction and command delegation -- it doesn't contain any security logic. This design keeps the attack surface small and allows the security-critical blueprint to evolve independently.

**Python Blueprint:** A versioned artifact with its own release cycle that the plugin resolves, verifies (via digest validation), and executes as a subprocess. The blueprint handles all OpenShell CLI interactions: sandbox creation, policy configuration, and inference setup. It follows a five-stage lifecycle: Resolve (version constraint checking), Verify (digest validation), Plan (resource determination), Apply (CLI command execution), and Status (state reporting).

The blueprint separation exists because security policies need to evolve faster than the CLI. When a new vulnerability class is discovered or a policy improvement ships, only the blueprint needs updating. The plugin's digest verification ensures you always run an authentic blueprint.

### Three Operational Levels

**Host Machine Level:** Stores credentials (`~/.nemoclaw/credentials.json`), sandbox metadata (`~/.nemoclaw/sandboxes.json`), and runs messaging bridge processes for Telegram, Discord, and Slack integration. The host level never exposes credentials to the sandbox -- OpenShell manages credential injection at the gateway level.

**OpenShell Runtime Level:** Provides the gateway (credential management and inference proxying), the policy engine (network, filesystem, process enforcement), and the privacy router (local vs. cloud inference routing). This is the enforcement boundary -- all agent actions must pass through OpenShell before reaching the outside world.

**Sandbox Container Level:** The isolated environment where the OpenClaw agent and NemoClaw plugin actually run. The container is built from the blueprint's hardened Dockerfile with capability drops and least-privilege rules. Read-write access is limited to `/sandbox` and `/tmp`; system paths are read-only.

### Why This Architecture

The three-level split exists to solve a specific problem: how do you give an autonomous agent genuine capabilities (file I/O, code execution, network access) while maintaining security guarantees? The answer is the "firewall" pattern -- the OpenShell runtime sits between the agent and the world, enforcing policy on every interaction.

This is fundamentally different from Docker isolation alone. Standard containers isolate processes from the host but don't understand agent intent. NemoClaw's OpenShell layer provides agent-aware policy evaluation at the binary, destination, method, and path level. It can distinguish between "the agent is downloading a pip package" and "the agent is exfiltrating data to an unknown endpoint" and apply different policies to each.

### Protection Architecture

| Layer | What It Controls | Enforcement Mechanism | When Applied | Mutable? |
|-------|-----------------|----------------------|-------------|----------|
| Network | Outbound connections | YAML allowlist + namespace isolation | Runtime | Hot-reloadable |
| Filesystem | File read/write access | Landlock LSM | Sandbox creation | Locked |
| Process | System calls, privilege escalation | seccomp filters + capability drops | Sandbox creation | Locked |
| Inference | Model API routing | OpenShell gateway interception | Runtime | Hot-reloadable |

The split between locked and hot-reloadable layers is deliberate. Filesystem and process restrictions are immutable after sandbox creation because these are the foundational security boundaries -- allowing runtime changes would enable a compromised agent to weaken its own restrictions. Network and inference policies are hot-reloadable because operational needs change: you might need to approve a new API endpoint or switch inference providers without restarting the agent.

### Data Flow

1. User sends a message to the agent (via CLI, TUI, or messaging bridge)
2. OpenClaw agent processes the message and decides on actions
3. If the agent makes an inference call, OpenShell intercepts it at the gateway
4. The privacy router evaluates the request against inference policies
5. The request is routed to the appropriate provider (local Nemotron, cloud API, etc.)
6. If the agent attempts a network connection, OpenShell checks the egress allowlist
7. Blocked connections surface in the terminal UI for operator approval
8. Approved endpoints persist for the session but don't modify baseline policy
9. All file operations are confined to `/sandbox` and `/tmp` by Landlock
10. All system calls are filtered by seccomp -- dangerous calls are blocked silently
