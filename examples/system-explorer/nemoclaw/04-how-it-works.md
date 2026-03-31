## How It Works
<!-- level: intermediate -->
<!-- references:
- [How NemoClaw Works](https://docs.nvidia.com/nemoclaw/latest/about/how-it-works.html) | official-docs
- [NemoClaw Architecture](https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html) | official-docs
- [OpenShell Technical Blog](https://developer.nvidia.com/blog/run-autonomous-self-evolving-agents-more-safely-with-nvidia-openshell/) | blog
-->

### Onboarding Flow

When you run `nemoclaw onboard`, the system executes a sequential creation process that provisions a fully secured agent environment in a single command.

**Step 1 -- Plugin Initialization:** The TypeScript plugin validates your system environment (Node.js version, container runtime availability, disk space) and collects your inference provider credentials interactively. Credentials are stored on the host at `~/.nemoclaw/credentials.json` and never enter the sandbox.

**Step 2 -- Blueprint Resolution:** The plugin checks the latest blueprint version against its version constraints, downloads the blueprint artifact, and verifies its cryptographic digest. This prevents supply-chain attacks where a tampered blueprint could weaken security policies.

**Step 3 -- Resource Planning:** The blueprint evaluates available compute resources (CPU cores, RAM, GPU availability) to determine optimal configuration. On GPU-equipped machines, it can configure local Nemotron inference. On CPU-only systems, it defaults to cloud inference providers.

**Step 4 -- Sandbox Creation:** The blueprint calls OpenShell CLI commands to create an isolated container from the hardened Dockerfile. During creation, Landlock filesystem policies and seccomp process filters are applied and locked -- these cannot be changed after this point. The sandbox image includes the OpenClaw runtime, the NemoClaw plugin, and the matching model reference for inference routing.

**Step 5 -- Policy Application:** Network egress policies (defined in `openclaw-sandbox.yaml`) and inference routing policies are applied. These are the hot-reloadable policies that operators can adjust at runtime.

**Step 6 -- Startup Verification:** The blueprint runs health checks to confirm the sandbox is operational, the inference provider is reachable, and all policy layers are active. The sandbox is now ready for connections.

### Inference Routing

Every time the OpenClaw agent needs to call a language model, the request never goes directly to the provider. Instead, it follows this path:

1. The agent constructs an inference request (prompt + context) inside the sandbox
2. The NemoClaw plugin's registered inference provider intercepts the call
3. The request is forwarded to the OpenShell gateway (running outside the sandbox)
4. The privacy router evaluates the request against configured policies
5. Based on the policy, the request is routed to either:
   - A local model (Nemotron via Ollama or vLLM) for privacy-sensitive tasks
   - A cloud endpoint (NVIDIA Endpoints, OpenAI, Anthropic, Gemini) for tasks requiring frontier capabilities
6. The provider credentials are injected at the gateway level -- the agent never sees API keys
7. The response flows back through the gateway into the sandbox

The privacy router's default model is `nvidia/nemotron-3-super-120b-a12b` via NVIDIA Cloud API. Local inference via Ollama and vLLM is available but experimental. The key architectural decision is that the routing logic lives outside the sandbox -- the agent cannot influence which provider handles its requests.

### Network Policy Enforcement

NemoClaw uses a deny-by-default network model. All outbound connections from the sandbox are blocked unless explicitly allowed in the YAML policy file.

When the agent attempts to reach a blocked endpoint:
1. OpenShell intercepts the connection attempt at the network namespace boundary
2. The connection is blocked and logged
3. The blocked request surfaces in the operator's terminal UI (accessible via `openshell term`)
4. The operator can approve the endpoint for the current session
5. Session-approved endpoints persist until the sandbox restarts but do not modify the baseline policy file

This approach gives operators real-time visibility into what the agent is trying to access. Over time, operators build up their allowlist by observing legitimate access patterns, creating a policy that matches actual usage without over-permitting.

### Filesystem Isolation

The sandbox filesystem is enforced by Landlock Linux Security Module (LSM):

- **Read-write access:** `/sandbox` (agent working directory) and `/tmp` (temporary files)
- **Read-only access:** System paths (`/usr`, `/lib`, `/etc`, etc.)
- **No access:** Everything else -- including the host filesystem, other containers, and NemoClaw's own credential stores

This is locked at sandbox creation time and cannot be modified at runtime. Even if the agent finds a vulnerability in OpenClaw or the NemoClaw plugin, Landlock prevents filesystem escalation at the kernel level.

### Process Isolation

The seccomp filter profile drops dangerous system calls and prevents privilege escalation:

- The agent cannot use `setuid`, `setgid`, or related calls to gain elevated privileges
- Dangerous system calls (e.g., `ptrace`, `mount`, `reboot`) are blocked
- Docker capabilities are dropped to the minimum required set
- The container runs as a non-root user

Like filesystem isolation, these restrictions are applied at sandbox creation and are immutable.

### State Management and Migration

NemoClaw supports migrating agent state between machines -- for example, moving an agent from a development laptop to a production GPU server. The migration process:

1. Creates a snapshot of the sandbox state
2. Strips all credentials from the snapshot (credentials are host-specific)
3. Exports the snapshot as a portable artifact
4. On the target machine, the snapshot is imported and re-provisioned with local credentials

Credential stripping during migration prevents accidental exposure of API keys or tokens when sharing agent states across environments.

### Messaging Bridges

NemoClaw can expose the sandboxed agent through external messaging platforms (Telegram, Discord, Slack) via host-side bridge processes. The bridges:

- Run on the host, not inside the sandbox
- Forward messages between the external platform and the agent
- Are subject to the same network policies as other connections
- Can be configured via environment variables

The bridges run outside the sandbox so that messaging platform credentials stay on the host. The agent sees incoming messages but cannot directly access the messaging platform's API.
