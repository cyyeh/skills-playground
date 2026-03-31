## Implementation Details
<!-- level: advanced -->
<!-- references:
- [NemoClaw Quickstart Guide](https://docs.nvidia.com/nemoclaw/latest/get-started/quickstart.html) | official-docs
- [NemoClaw CLI Commands Reference](https://docs.nvidia.com/nemoclaw/latest/reference/commands.html) | official-docs
- [NemoClaw Inference Profiles](https://docs.nvidia.com/nemoclaw/latest/reference/inference-profiles.html) | official-docs
- [NemoClaw Network Policies](https://github.com/NVIDIA/NemoClaw/blob/main/docs/reference/network-policies.md) | github
-->

### System Requirements

**Hardware:**
- CPU: 4+ vCPU (minimum 4)
- RAM: 16 GB recommended (8 GB minimum)
- Disk: 40 GB free (20 GB minimum)
- Sandbox image size: ~2.4 GB compressed

**Software:**
- Ubuntu 22.04 LTS or later (primary supported platform)
- Node.js 22.16+
- npm 10+
- Container runtime: Docker (primary path)

**Platform Support:**

| Platform | Runtime | Notes |
|----------|---------|-------|
| Linux | Docker | Primary supported path |
| macOS (Apple Silicon) | Colima, Docker Desktop | Requires Xcode CLT |
| macOS (Intel) | Podman | Not yet supported |
| Windows WSL | Docker Desktop | WSL backend required |
| DGX Spark | Docker | Requires cgroup v2 config |

### Installation

NemoClaw provides a one-line installer that handles all dependencies:

```bash
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash
```

The installer automates Node.js installation (if not present), sandbox creation, inference configuration, and security policy application. It launches an interactive onboarding wizard that walks through provider selection and credential setup.

To uninstall:

```bash
curl -fsSL https://raw.githubusercontent.com/NVIDIA/NemoClaw/refs/heads/main/uninstall.sh | bash
```

Uninstall flags include `--yes` (skip confirmation), `--keep-openshell` (retain the OpenShell binary), and `--delete-models` (remove downloaded local models).

### Key CLI Commands

```bash
# Initial onboarding — creates sandbox, configures inference and policies
nemoclaw onboard

# Connect to a running sandbox (interactive shell)
nemoclaw my-assistant connect

# Check sandbox health and status
nemoclaw my-assistant status

# Stream sandbox logs
nemoclaw my-assistant logs --follow

# Interactive chat TUI
openclaw tui

# Single-message CLI interaction
openclaw agent --agent main --local -m "Summarize today's news" --session-id test
```

### Inference Provider Configuration

During onboarding, NemoClaw validates and configures the selected inference provider. Supported providers:

**Production-ready:**
- NVIDIA Endpoints (OpenAI-compatible, hosted on `integrate.api.nvidia.com`)
- OpenAI (native OpenAI protocol)
- Anthropic (uses `anthropic-messages` protocol)
- Google Gemini (OpenAI-compatible via Google's endpoint)
- Custom OpenAI-compatible endpoints (proxies, gateways)
- Custom Anthropic-compatible endpoints

**Experimental (requires `NEMOCLAW_EXPERIMENTAL=1`):**
- Local NVIDIA NIM (GPU-dependent)
- Local vLLM (running on `localhost:8000`)
- Local Ollama (when installed on the host)

Validation differs by provider type. OpenAI-compatible providers are tested against `/responses` then `/chat/completions`. Anthropic providers validate against `/v1/messages`. Custom endpoints receive a real inference request because many proxies lack a reliable `/models` endpoint.

### Network Policy Configuration

The baseline policy lives in `nemoclaw-blueprint/policies/openclaw-sandbox.yaml`. It follows a deny-all-by-default model with explicit allowlist entries:

```yaml
# Example policy structure (simplified)
network:
  egress:
    default: deny
    allow:
      - host: api.openai.com
        port: 443
        protocol: https
      - host: integrate.api.nvidia.com
        port: 443
        protocol: https
```

Preset policy files for common integrations are available in `nemoclaw-blueprint/policies/presets/`:
- PyPI (package installation)
- Docker Hub (container image pulls)
- Slack (messaging bridge)
- Jira (issue tracking integration)

To add a preset during runtime:

```bash
openshell policy apply --preset slack
```

Policies are hot-reloadable — changes take effect without restarting the sandbox. Runtime approvals (via the TUI) persist for the current session only and do not modify the baseline YAML.

### Sandbox Hardening Details

The blueprint creates a container with the following security measures:

**Capability Drops:** All Linux capabilities are dropped except the minimum set required for the agent to function. This prevents privilege escalation even if the agent exploits a container runtime vulnerability.

**Filesystem Mounts:**
- `/sandbox` — Read-write, agent's working directory
- `/tmp` — Read-write, temporary storage
- All system paths — Read-only (prevents modification of binaries, libraries, or configuration)

**Process Limits:** Resource limits (CPU, memory, open file descriptors) are applied to prevent the agent from consuming host resources through fork bombs or memory exhaustion attacks.

### Host-Side Configuration Files

```
~/.nemoclaw/
  credentials.json    # Provider API keys (never enters sandbox)
  sandboxes.json      # Sandbox metadata and version tracking

~/.openclaw/
  openclaw.json       # OpenClaw configuration snapshots
```

### Environment Variables

Key environment variables for messaging bridge configuration:

```bash
NEMOCLAW_TELEGRAM_TOKEN=<bot-token>
NEMOCLAW_TELEGRAM_CHAT_IDS=<allowed-chat-ids>
NEMOCLAW_DISCORD_TOKEN=<bot-token>
NEMOCLAW_SLACK_TOKEN=<bot-token>
NEMOCLAW_EXPERIMENTAL=1  # Enable experimental providers
```
