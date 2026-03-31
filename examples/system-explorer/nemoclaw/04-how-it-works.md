## How It Works
<!-- level: intermediate -->
<!-- references:
- [How NemoClaw Works](https://docs.nvidia.com/nemoclaw/latest/about/how-it-works.html) | official-docs
- [NemoClaw Inference Profiles](https://docs.nvidia.com/nemoclaw/latest/reference/inference-profiles.html) | official-docs
- [NemoClaw Network Policies](https://github.com/NVIDIA/NemoClaw/blob/main/docs/reference/network-policies.md) | github
-->

NemoClaw orchestrates a full security stack in a single command. Understanding the internal mechanisms — from sandbox creation to runtime policy enforcement — reveals how each layer protects against different threat vectors.

### Onboarding Flow

When you run `nemoclaw onboard`, the system executes a guided multi-step process:

1. **Blueprint Resolution:** The plugin locates the blueprint artifact (from a registry or local cache) and checks the version against minimum OpenShell and OpenClaw compatibility requirements.
2. **Digest Verification:** The blueprint's cryptographic digest is validated to ensure the artifact has not been tampered with since publication.
3. **Resource Planning:** The blueprint determines which OpenShell resources are needed — a gateway, inference providers, a sandbox container, an inference route, and a network policy.
4. **Credential Collection:** The onboarding wizard prompts for inference provider selection and API credentials. Credentials are stored on the host at `~/.nemoclaw/credentials.json` and never enter the sandbox.
5. **Sandbox Creation:** The blueprint invokes `openshell sandbox create` with the hardened Dockerfile, security policies, and capability drops. The sandbox image is approximately 2.4 GB compressed.
6. **Policy Application:** Network egress rules from `openclaw-sandbox.yaml` are loaded into the OpenShell policy engine. The agent starts in a "deny all except explicitly allowed" state.

### Inference Routing Mechanism

Inference requests follow a controlled path that keeps credentials secure:

1. The agent inside the sandbox makes a standard model API call to `inference.local` (a virtual endpoint visible only within the sandbox's network namespace).
2. OpenShell intercepts the request at the network namespace boundary and routes it to the OpenShell gateway running on the host.
3. The gateway looks up the configured inference route, attaches the provider's API key from the host-side credential store, and forwards the request to the actual provider endpoint (NVIDIA Endpoints, OpenAI, Anthropic, Google Gemini, Ollama, or a custom endpoint).
4. The provider's response flows back through the gateway to the agent. At no point does the agent see the raw API key.

Provider validation during onboarding differs by type: OpenAI-compatible providers are tested against `/responses` then `/chat/completions`; Anthropic providers validate against `/v1/messages`. For custom endpoints, NemoClaw sends a real inference request because many proxies do not expose a reliable `/models` endpoint.

### Security Enforcement Layers

Four independent defense layers operate simultaneously:

**Filesystem Isolation (Landlock)**
When the sandbox starts, the `openshell-sandbox` supervisor fetches a Landlock policy from the policy engine over gRPC and applies it to the agent child process. The agent can read and write `/sandbox` and `/tmp`; all system paths are mounted read-only. The policy is locked at creation time and cannot be modified by the agent process.

**Syscall Filtering (seccomp)**
A seccomp BPF filter is applied when the sandbox container is created. It runs in allowlist mode, permitting only the syscalls the agent needs for normal operation and blocking everything else. The filter controls individual syscall arguments at a fine-grained level. Like filesystem policies, seccomp rules are locked at creation and cannot be relaxed by the agent.

**Network Namespace Isolation**
Each sandbox gets its own network namespace, giving the agent a completely isolated view of the network. The agent cannot see the host's network interfaces, routing tables, or other containers. Every TCP connection the agent makes is forced through an HTTP CONNECT proxy operated by OpenShell — the agent cannot detect or bypass this interception.

**Inference Control**
All model API calls are intercepted and routed through the gateway. The agent communicates only with `inference.local` — there is no direct path to any external model provider. Inference routing is hot-reloadable at runtime, allowing operators to switch providers or models without restarting the sandbox.

### Runtime Policy Enforcement

Network policies operate at runtime with a dynamic approval workflow:

1. The agent attempts to connect to an external host not listed in the baseline policy.
2. OpenShell blocks the connection at the network namespace boundary and logs the attempt (host, port, requesting binary).
3. The blocked request appears in the operator's TUI (`openshell term`) with full context.
4. The operator can approve or deny the request. Approved endpoints persist for the current session but do not modify the baseline policy file.
5. To permanently allow an endpoint, the operator edits the `openclaw-sandbox.yaml` policy and applies it via the CLI.

NemoClaw ships preset policy files for common integrations (PyPI, Docker Hub, Slack, Jira) in `nemoclaw-blueprint/policies/presets/`.

### Messaging Bridges

NemoClaw supports connecting the sandboxed agent to external messaging platforms via host-side bridge processes:

- **Telegram, Discord, Slack:** Bridge processes run on the host (outside the sandbox) and relay messages to/from the agent through the sandbox's exposed chat interface. This architecture ensures that messaging credentials remain on the host and the agent cannot directly access messaging APIs.

Environment variables configure the messaging integrations (Telegram bot token, chat IDs, allowed users). The bridges communicate with the agent through the sandbox's internal API, maintaining the security boundary.

### State Migration

NemoClaw supports moving agent state between machines through a secure migration process:

1. **Export:** The agent's state (session history, learned skills, configuration) is serialized and credentials are stripped from the export.
2. **Integrity Check:** A hash is computed over the exported state to detect tampering during transit.
3. **Import:** On the destination machine, the state is verified against the integrity hash, credentials are re-provisioned from the local credential store, and the sandbox is recreated from the same blueprint version.
