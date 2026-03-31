## Implementation Details
<!-- level: advanced -->
<!-- references:
- [NemoClaw Quickstart Guide](https://docs.nvidia.com/nemoclaw/latest/get-started/quickstart.html) | official-docs
- [NemoClaw GitHub Repository](https://github.com/NVIDIA/NemoClaw) | github
- [NemoClaw Architecture](https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html) | official-docs
- [DeepWiki: Getting Started with NemoClaw](https://deepwiki.com/NVIDIA/NemoClaw/2-getting-started) | blog
-->

### Getting Started

**Prerequisites:**
- Linux (Ubuntu 22.04 LTS or later) or macOS with Docker
- Node.js 22.16 or later, npm 10 or later
- A supported container runtime: Docker (primary), Colima, Podman, or Docker Desktop
- OpenShell installed
- Hardware: 4 vCPU minimum, 8 GB RAM minimum (16 GB recommended), 20 GB disk (40 GB recommended)

**Installation (one command):**

```bash
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash
```

If you use nvm or fnm, reload your shell after installation:

```bash
source ~/.bashrc  # or ~/.zshrc for zsh
```

**Onboarding a new agent:**

```bash
nemoclaw onboard
```

This launches an interactive wizard that:
1. Validates your system environment
2. Prompts for an inference provider (NVIDIA Endpoints, OpenAI, Anthropic, Gemini, or local Ollama)
3. Collects API credentials
4. Downloads and verifies the blueprint
5. Creates the sandboxed OpenClaw instance
6. Runs health checks

**Connecting to your agent:**

```bash
nemoclaw my-assistant connect
```

**Checking status:**

```bash
nemoclaw my-assistant status
```

**Viewing logs:**

```bash
nemoclaw my-assistant logs --follow
```

**Opening the monitoring TUI:**

```bash
openclaw tui
```

**Sending a single message:**

```bash
openclaw agent --agent main --local -m "hello" --session-id test
```

**Uninstalling:**

```bash
curl -fsSL https://raw.githubusercontent.com/NVIDIA/NemoClaw/refs/heads/main/uninstall.sh | bash
```

Flags: `--yes` (skip confirmation), `--keep-openshell` (preserve the runtime), `--delete-models` (remove downloaded models)

### Project Structure

```
NemoClaw/
├── bin/                        # CLI entry point and CommonJS modules
├── nemoclaw/                   # TypeScript plugin (Commander extension)
│   └── src/
│       ├── blueprint/          # Execution runner, snapshots, SSRF validation
│       ├── commands/           # CLI commands and state migration
│       └── onboard/            # Initial setup configuration
├── nemoclaw-blueprint/         # Blueprint YAML and network policy definitions
├── scripts/                    # Installation utilities and automation
├── test/                       # Integration and end-to-end testing
├── docs/                       # Sphinx/MyST documentation
├── k8s/                        # Kubernetes configurations
├── ci/                         # Continuous integration setup
├── Dockerfile                  # Sandbox container definition
├── Dockerfile.base             # Base image for the sandbox
├── package.json                # Node.js dependencies
├── pyproject.toml              # Python dependencies (blueprint)
├── tsconfig.cli.json           # TypeScript configuration
├── install.sh                  # Installer script
├── uninstall.sh                # Removal script
├── CONTRIBUTING.md             # Development guidelines
├── SECURITY.md                 # Vulnerability reporting
└── LICENSE                     # Apache 2.0
```

### Source Code Walkthrough

**CLI Command Registration (TypeScript Plugin):**

```typescript
// source: nemoclaw/src/commands/index.ts:L1-L35
// github: NVIDIA/NemoClaw
// tag: main

import { Command } from 'commander';
import { onboard } from '../onboard/wizard';
import { connectSandbox } from './connect';
import { getSandboxStatus } from './status';
import { tailLogs } from './logs';
import { migrateSandbox } from './migrate';

export function registerCommands(program: Command): void {
  program
    .command('onboard')
    .description('Set up a new NemoClaw sandbox')
    .action(onboard);

  program
    .command('<name> connect')
    .description('Connect to a running sandbox')
    .action(connectSandbox);

  program
    .command('<name> status')
    .description('Check sandbox health')
    .action(getSandboxStatus);

  program
    .command('<name> logs')
    .option('--follow', 'Stream logs in real time')
    .action(tailLogs);

  program
    .command('<name> migrate')
    .description('Export sandbox state for migration')
    .action(migrateSandbox);
}
```

The CLI is built with Commander.js, a standard Node.js command framework. Each subcommand delegates to a focused module, keeping the command registration thin and testable.

**Blueprint Resolution and Verification:**

```typescript
// source: nemoclaw/src/blueprint/resolver.ts:L10-L55
// github: NVIDIA/NemoClaw
// tag: main

import { createHash } from 'crypto';
import { readFile } from 'fs/promises';

interface BlueprintManifest {
  version: string;
  digest: string;
  minPluginVersion: string;
  artifacts: string[];
}

export async function resolveBlueprint(
  constraint: string
): Promise<BlueprintManifest> {
  // Fetch the manifest index from the blueprint registry
  const index = await fetchManifestIndex();

  // Find the latest version matching the constraint
  const matched = index.versions
    .filter(v => satisfiesConstraint(v.version, constraint))
    .sort(byVersionDescending)[0];

  if (!matched) {
    throw new Error(
      `No blueprint version satisfies constraint "${constraint}"`
    );
  }

  return matched;
}

export async function verifyBlueprint(
  path: string,
  expectedDigest: string
): Promise<boolean> {
  const content = await readFile(path);
  const actualDigest = createHash('sha256')
    .update(content)
    .digest('hex');

  if (actualDigest !== expectedDigest) {
    throw new Error(
      'Blueprint digest mismatch -- possible tampering detected'
    );
  }

  return true;
}
```

The resolver follows a trust-but-verify pattern: it downloads from the registry but validates the SHA-256 digest before execution. This prevents supply-chain attacks where a compromised registry could serve a weakened blueprint.

**SSRF Validation:**

```typescript
// source: nemoclaw/src/blueprint/ssrf.ts:L1-L30
// github: NVIDIA/NemoClaw
// tag: main

import { URL } from 'url';
import { isIPv4 } from 'net';

const BLOCKED_RANGES = [
  '127.0.0.0/8',     // loopback
  '10.0.0.0/8',      // private class A
  '172.16.0.0/12',   // private class B
  '192.168.0.0/16',  // private class C
  '169.254.0.0/16',  // link-local
  '0.0.0.0/8',       // current network
];

export function validateUrl(rawUrl: string): boolean {
  const parsed = new URL(rawUrl);

  // Block non-HTTP(S) schemes
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    return false;
  }

  // Resolve hostname and check against blocked ranges
  const ip = resolveHostname(parsed.hostname);
  if (ip && isBlockedRange(ip, BLOCKED_RANGES)) {
    return false;
  }

  return true;
}
```

SSRF (Server-Side Request Forgery) validation prevents the agent from tricking NemoClaw into making requests to internal network addresses. This is a critical defense when the agent can influence URLs (e.g., fetching web content).

**Sandbox Network Policy (YAML):**

```yaml
# source: nemoclaw-blueprint/openclaw-sandbox.yaml:L1-L25
# github: NVIDIA/NemoClaw
# tag: main

apiVersion: openshell.nvidia.com/v1alpha1
kind: SandboxPolicy
metadata:
  name: openclaw-baseline
spec:
  network:
    egress:
      default: deny
      allowlist:
        - host: "api.nvidia.com"
          ports: [443]
          protocol: https
        - host: "*.openai.com"
          ports: [443]
          protocol: https
        - host: "pypi.org"
          ports: [443]
          protocol: https
  filesystem:
    readWrite:
      - /sandbox
      - /tmp
    readOnly:
      - /usr
      - /lib
      - /etc
  process:
    capabilities:
      drop: [ALL]
      add: [NET_BIND_SERVICE]
    seccomp: restricted
```

The policy file uses a Kubernetes-style declarative format familiar to platform engineers. The deny-by-default egress policy is the foundation: only explicitly listed endpoints are reachable from the sandbox.

### Technology Stack

| Component | Technology | Percentage of Codebase |
|-----------|-----------|----------------------|
| CLI entry point & modules | JavaScript | 51.8% |
| Installation & automation | Shell | 30.8% |
| Plugin core | TypeScript | 13.4% |
| Blueprint orchestration | Python | 3.4% |
| Configuration | YAML, JSON | 0.6% |

### Key Design Decisions

**Why TypeScript for the plugin?** The plugin runs in-process with the OpenClaw gateway, which is a Node.js application. TypeScript gives type safety for the CLI while remaining compatible with OpenClaw's runtime.

**Why Python for the blueprint?** The blueprint interacts heavily with Docker, OpenShell CLI tools, and system administration tasks where Python's subprocess management and ecosystem (PyYAML, cryptography libraries) are well-suited.

**Why separate plugin and blueprint?** Different release cadences. Security policies (blueprint) need to ship faster than UX changes (plugin). The plugin simply downloads, verifies, and executes the blueprint.
