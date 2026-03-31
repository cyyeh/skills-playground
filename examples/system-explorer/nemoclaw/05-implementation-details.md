## Implementation Details
<!-- level: advanced -->
<!-- references:
- [NemoClaw Quickstart](https://docs.nvidia.com/nemoclaw/latest/get-started/quickstart.html) | official-docs
- [NemoClaw Commands Reference](https://docs.nvidia.com/nemoclaw/latest/reference/commands.html) | official-docs
- [NemoClaw GitHub Source](https://github.com/NVIDIA/NemoClaw) | github
-->

### Getting Started

The fastest path from zero to a running sandboxed OpenClaw instance requires a Linux machine (Ubuntu 22.04+), Docker, and a single command:

```bash
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash
```

This installer checks prerequisites (Node.js 22.16+, npm 10+, Docker), installs them if missing, and launches an interactive onboarding wizard. The wizard walks through three steps: selecting an inference provider, configuring credentials (stored on the host, never in the sandbox), and applying security policies. Once complete, connect to the sandbox:

```bash
nemoclaw my-assistant connect
```

Inside the sandbox, interact with the agent using the OpenClaw TUI:

```bash
openclaw tui
```

Or send a single message from the command line:

```bash
openclaw agent --agent main --local -m "Explain this codebase" --session-id test
```

**Hardware minimums**: 4 vCPU, 8 GB RAM, 20 GB disk. Recommended: 4+ vCPU, 16 GB RAM, 40 GB disk (the sandbox image alone is ~2.4 GB compressed).

**Platform support**: Docker on Linux is the primary path. macOS (Apple Silicon) is supported via Colima or Docker Desktop. Windows requires Docker Desktop with WSL backend. NVIDIA DGX Spark is supported with additional cgroup v2 configuration via `nemoclaw setup-spark`.

### Configuration Essentials

| Config | File / Location | What It Controls | When to Change |
|--------|----------------|-----------------|----------------|
| Network policy | `nemoclaw-blueprint/policies/openclaw-sandbox.yaml` | Allowed outbound endpoints, HTTP methods, ports | When the agent needs access to new APIs or services |
| Inference provider | Set during `nemoclaw onboard` | Which LLM backend handles model calls | When switching between cloud and local inference |
| Blueprint version | `blueprint.yaml` in the blueprint artifact | Sandbox image version and configuration | When upgrading to a new NemoClaw release |
| Sandbox name | Set during `nemoclaw onboard` | Identifier for the sandbox instance (RFC 1123 format) | Once, during initial setup |
| Telegram bridge | `TELEGRAM_BOT_TOKEN` environment variable | Messaging bridge to Telegram | When enabling always-on Telegram access |
| Filesystem boundaries | Enforced by Landlock policies in the sandbox | Read-write access limited to `/sandbox` and `/tmp` | Rarely -- modifying this weakens the security model |
| TLS enforcement | Hardcoded in policy engine | All connections must use port 443 with TLS | Not configurable -- this is by design |

### Code Patterns

**Checking sandbox status programmatically:**

```bash
# List all registered sandboxes with their model, provider, and policy details
nemoclaw list

# Check a specific sandbox's health and inference configuration
nemoclaw my-assistant status

# Stream logs in real time for debugging
nemoclaw my-assistant logs --follow
```

**Managing network policies at runtime:**

```bash
# View available policy presets and which are currently applied
nemoclaw my-assistant policy-list

# Add a policy preset to extend network access (e.g., allow PyPI)
nemoclaw my-assistant policy-add

# Apply a custom policy file to a running sandbox without restart
openshell policy set custom-policy.yaml

# Monitor and approve/deny blocked requests in real time
openshell term
```

**Deploying to a remote GPU instance:**

```bash
# Deploy to a remote GPU server via Brev (experimental)
nemoclaw deploy my-remote-agent
```

**Uninstalling cleanly:**

```bash
# Full removal with confirmation prompts
curl -fsSL https://raw.githubusercontent.com/NVIDIA/NemoClaw/refs/heads/main/uninstall.sh | bash

# Automated removal preserving OpenShell and downloaded models
curl -fsSL https://raw.githubusercontent.com/NVIDIA/NemoClaw/refs/heads/main/uninstall.sh | bash -s -- --yes --keep-openshell --delete-models
```

### Source Code Walkthrough

#### CLI Entry Point -- Implementation

The NemoClaw CLI is a single JavaScript file that serves as the orchestrator for all user-facing operations. It parses commands, dispatches to the appropriate library module, and manages the lifecycle of sandbox instances.

```javascript
// source: bin/nemoclaw.js
// github: NVIDIA/NemoClaw
// tag: v0.0.1
// Main CLI entry point -- dispatches commands to library modules
// Commands: onboard, list, deploy, connect, status, logs, destroy,
//           policy-add, policy-list, start, stop, setup-spark
```

#### Blueprint Resolution and Verification -- Implementation

The runner module handles the five-stage blueprint lifecycle: resolve, verify, plan, apply, status. It downloads the blueprint artifact, checks its digest, and orchestrates OpenShell resource creation.

```javascript
// source: bin/lib/runner.js
// github: NVIDIA/NemoClaw
// tag: v0.0.1
// Implements the blueprint lifecycle pipeline:
// 1. Resolve version constraints from the registry
// 2. Verify artifact digest against expected value
// 3. Plan required resource changes (diff current vs desired)
// 4. Apply changes via OpenShell CLI commands
// 5. Report final system state
```

#### Credential Management -- Implementation

The credentials module strips sensitive data from configuration before it enters the sandbox. It scans for known credential patterns in environment variables, config objects, and log lines.

```javascript
// source: bin/lib/credentials.js
// github: NVIDIA/NemoClaw
// tag: v0.0.1
// Credential sanitization layer
// - Strips API keys from config objects before sandbox injection
// - Scans environment variables for known credential patterns
// - Ensures credentials remain host-side only
```

#### Inference Configuration -- Implementation

The inference-config module manages provider selection, validation, and routing setup. It implements the per-provider validation strategies (OpenAI-compatible, Anthropic, NVIDIA, custom).

```javascript
// source: bin/lib/inference-config.js
// github: NVIDIA/NemoClaw
// tag: v0.0.1
// Inference provider configuration and validation
// - Supports 6 provider categories (NVIDIA, OpenAI, Anthropic, Gemini, custom, local)
// - Validates provider endpoints before sandbox creation
// - Configures inference.local routing through OpenShell gateway
```

#### Network Policy Engine -- Implementation

The policies module parses the YAML policy file and translates it into OpenShell policy commands. It handles both static policy application during onboarding and dynamic policy updates to running sandboxes.

```javascript
// source: bin/lib/policies.js
// github: NVIDIA/NemoClaw
// tag: v0.0.1
// Network policy management
// - Parses openclaw-sandbox.yaml for allowed endpoint definitions
// - Translates YAML rules into OpenShell policy set commands
// - Manages policy presets (add, list, apply)
// - Supports runtime policy updates without sandbox restart
```

#### Onboarding Flow -- Implementation

The onboard module implements the interactive setup wizard that walks operators through provider selection, credential storage, and initial policy configuration.

```javascript
// source: bin/lib/onboard.js
// github: NVIDIA/NemoClaw
// tag: v0.0.1
// Interactive onboarding wizard
// - Guided credential validation and provider selection
// - Manages onboard-session state for resume capability
// - Calls runner.js to execute blueprint lifecycle after configuration
```

### Deployment Considerations

**Sizing**: For a single always-on agent, the minimum hardware (4 vCPU, 8 GB RAM) is sufficient for lightweight inference via cloud providers. If running local inference with Ollama or NVIDIA NIM, the recommended configuration is 16+ GB RAM and an NVIDIA GPU for acceptable response times.

**Monitoring**: Use `nemoclaw <name> logs --follow` for real-time log streaming and `openshell term` for the interactive TUI that shows network activity and pending approval requests. The TUI is the primary operational interface for understanding what the agent is doing at any given moment.

**Backup and Restore**: NemoClaw's documentation includes a dedicated workspace backup and restore guide. The agent's working directory (`/sandbox`) is the primary state to preserve. Blueprint configurations should be version-controlled separately.

**Upgrade Path**: Because NemoClaw is in alpha with breaking changes between releases, upgrades should be treated as full re-onboarding. Destroy the existing sandbox, update the CLI, and run `nemoclaw onboard` again. The blueprint versioning system ensures that the new configuration is explicitly applied rather than silently merged.

**Security Hardening**: Beyond the defaults, NemoClaw's documentation includes a sandbox hardening guide that covers additional measures for high-security environments. The base Dockerfile already applies capability drops and least-privilege rules, but operators can add further seccomp profile restrictions and tighten Landlock policies.
