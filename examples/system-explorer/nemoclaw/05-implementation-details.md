## Implementation Details
<!-- level: advanced -->
<!-- references:
- [NemoClaw GitHub](https://github.com/NVIDIA/NemoClaw) | github
- [NemoClaw Architecture](https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html) | official-docs
- [OpenClaw Agent Tools](https://docs.openclaw.ai/plugins/agent-tools) | official-docs
- [OpenClaw Sandboxing](https://docs.openclaw.ai/gateway/sandboxing) | official-docs
-->

### Language Composition

The NemoClaw codebase is a polyglot project reflecting its layered architecture:

- **JavaScript (50%):** CLI runtime, command handling, and plugin lifecycle
- **Shell (31.9%):** Installation scripts, container orchestration, and environment setup
- **TypeScript (14%):** Type-safe plugin code, blueprint runner, and CLI command definitions
- **Python (3.6%):** Blueprint orchestration and inference provider configuration

The Rust-based Policy Engine is provided as a compiled binary within the OpenShell runtime, not as source in the NemoClaw repository.

### Plugin Implementation

The TypeScript plugin integrates with OpenClaw's CLI via the Commander.js pattern:

```typescript
// NemoClaw CLI plugin registration
import { Command } from 'commander';

export function register(program: Command) {
  const nemoclaw = program
    .command('nemoclaw')
    .description('Manage NemoClaw sandboxes');

  nemoclaw
    .command('launch')
    .description('Launch a new NemoClaw sandbox')
    .option('--provider <provider>', 'Inference provider', 'nvidia')
    .option('--model <model>', 'Model identifier')
    .option('--policy <file>', 'Custom policy file')
    .action(async (options) => {
      const blueprint = await resolveBlueprint(options);
      await verifyDigest(blueprint);
      const plan = await planDeployment(blueprint, options);
      await applyPlan(plan);
      await reportStatus();
    });

  nemoclaw
    .command('status')
    .description('Show sandbox status')
    .action(async () => {
      const sandboxes = await loadSandboxRegistry();
      for (const sandbox of sandboxes) {
        console.log(formatStatus(sandbox));
      }
    });
}
```

### Blueprint Artifact Structure

A NemoClaw blueprint is an OCI-compliant artifact containing:

```
nemoclaw-blueprint/
  blueprint.yaml           # Version constraints and manifest
  policies/
    openclaw-sandbox.yaml  # Network, filesystem, process policies
  scripts/
    setup.sh               # Sandbox initialization script
    teardown.sh            # Cleanup script
  config/
    inference.json         # Provider routing configuration
    privacy-rules.json     # Sensitivity classification rules
```

### Policy File Format

The `openclaw-sandbox.yaml` is the primary security configuration:

```yaml
apiVersion: nemoclaw/v1alpha1
kind: SandboxPolicy
metadata:
  name: openclaw-default
  version: "1.0.0"

spec:
  filesystem:
    readWrite:
      - /sandbox
      - /tmp
    readOnly:
      - /usr
      - /lib
      - /etc
    denied:
      - /root
      - /home
      - /var/run/docker.sock

  network:
    egress:
      default: deny
      allow:
        - host: "api.nvidia.com"
          ports: [443]
          protocols: ["https"]
        - host: "huggingface.co"
          ports: [443]
          protocols: ["https"]
          methods: ["GET"]
      ssrf_protection:
        block_private_ips: true
        block_link_local: true
        resolve_dns: true

  process:
    max_processes: 64
    max_open_files: 1024
    capabilities:
      drop:
        - CAP_NET_RAW
        - CAP_SYS_ADMIN
        - CAP_SYS_PTRACE
        - CAP_NET_BIND_SERVICE
      add: []

  seccomp:
    profile: "restricted"
    additional_blocked_syscalls:
      - kexec_load
      - init_module
      - finit_module

  audit:
    log_level: "info"
    log_tool_calls: true
    log_network_requests: true
    log_inference_routing: true
    log_file_access: false  # Can be enabled for high-security environments
```

### Tool Registration and Schema Handling

Tools in OpenClaw use TypeBox for runtime-validated parameter schemas:

```typescript
import { Type, Static } from '@sinclair/typebox';

// Define a tool with strict parameter typing
const DatabaseQueryParams = Type.Object({
  query: Type.String({
    description: "SQL query to execute",
    maxLength: 10000,
  }),
  database: Type.String({
    description: "Target database name",
    pattern: "^[a-zA-Z_][a-zA-Z0-9_]*$",
  }),
  timeout_ms: Type.Optional(Type.Number({
    description: "Query timeout in milliseconds",
    minimum: 100,
    maximum: 30000,
    default: 5000,
  })),
});

type DatabaseQueryInput = Static<typeof DatabaseQueryParams>;

api.registerTool({
  name: "database_query",
  description: "Execute a read-only SQL query against a configured database",
  parameters: DatabaseQueryParams,

  async execute(_id: string, params: DatabaseQueryInput) {
    try {
      const result = await db.query(params.query, {
        database: params.database,
        timeout: params.timeout_ms ?? 5000,
        readOnly: true, // Enforce read-only at the driver level
      });

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            columns: result.columns,
            rows: result.rows.slice(0, 100), // Cap result size
            rowCount: result.rowCount,
            truncated: result.rowCount > 100,
          }),
        }],
      };
    } catch (error) {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            error: error.message,
            code: error.code,
          }),
        }],
        isError: true,
      };
    }
  },
});
```

### Inference Provider Configuration

The inference routing is configured in `~/.nemoclaw/credentials.json`:

```json
{
  "providers": {
    "nvidia": {
      "type": "nvidia-endpoints",
      "api_key": "nvapi-...",
      "model": "nvidia/nemotron-3-super-120b-a12b",
      "base_url": "https://integrate.api.nvidia.com/v1"
    },
    "ollama": {
      "type": "ollama",
      "base_url": "http://localhost:11434",
      "model": "nemotron:latest"
    },
    "custom": {
      "type": "openai-compatible",
      "api_key": "sk-...",
      "base_url": "https://api.openai.com/v1",
      "model": "gpt-4o"
    }
  },
  "routing": {
    "default": "nvidia",
    "sensitive": "ollama",
    "fallback": "custom"
  }
}
```

### Privacy Classification Rules

The Privacy Router uses a rule-based classification system:

```json
{
  "sensitivity_rules": [
    {
      "name": "pii_detection",
      "patterns": [
        "\\b\\d{3}-\\d{2}-\\d{4}\\b",
        "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b",
        "\\b\\d{4}[- ]?\\d{4}[- ]?\\d{4}[- ]?\\d{4}\\b"
      ],
      "classification": "sensitive",
      "action": "route_local"
    },
    {
      "name": "proprietary_code",
      "keywords": ["internal", "confidential", "proprietary", "trade_secret"],
      "classification": "sensitive",
      "action": "route_local"
    },
    {
      "name": "financial_data",
      "patterns": ["\\$[0-9,]+", "revenue", "profit", "loss", "balance_sheet"],
      "classification": "sensitive",
      "action": "route_local"
    }
  ],
  "default_classification": "non-sensitive",
  "default_action": "route_cloud"
}
```

### Error Handling and Retry Logic

NemoClaw implements error handling at multiple levels:

**Inference Layer:**
```typescript
async function routeInference(
  request: InferenceRequest,
  config: ProviderConfig,
): Promise<InferenceResponse> {
  const provider = selectProvider(request, config);

  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const response = await provider.complete(request);
      auditLog.record({
        type: 'inference',
        provider: provider.name,
        model: provider.model,
        sensitivity: request.classification,
        latency_ms: response.latency,
        tokens: response.usage,
      });
      return response;
    } catch (error) {
      if (error.retryable && attempt < 2) {
        await delay(Math.pow(2, attempt) * 1000); // Exponential backoff
        continue;
      }
      // Attempt fallback provider
      if (config.routing.fallback) {
        return routeInference(request, {
          ...config,
          routing: { ...config.routing, default: config.routing.fallback, fallback: undefined },
        });
      }
      throw error;
    }
  }
}
```

**Tool Execution Layer:**
- Tools return structured error responses (with `isError: true`) rather than throwing exceptions
- The agent receives error context and can retry with different parameters
- Persistent failures are logged to the audit trail and surfaced to the operator

**Network Layer:**
- Failed network requests are logged with full context (destination, policy rule, timestamp)
- Blocked requests generate operator alerts in real-time
- The Policy Engine maintains connection state for TCP half-open connection cleanup

### Audit Log Format

Every significant action generates a structured audit entry:

```json
{
  "timestamp": "2026-03-31T10:15:23.456Z",
  "session_id": "sess_abc123",
  "event_type": "tool_call",
  "tool_name": "http_request",
  "parameters": {
    "url": "https://api.example.com/health",
    "method": "GET"
  },
  "policy_evaluation": {
    "rule": "egress.allow[1]",
    "result": "allowed",
    "latency_us": 45
  },
  "execution": {
    "status": "success",
    "response_code": 200,
    "latency_ms": 142
  },
  "inference_routing": null
}
```

### Container Security Hardening

The sandbox container implements multiple isolation layers:

```dockerfile
# Simplified view of sandbox container security
FROM ubuntu:22.04 AS base

# Non-root user
RUN useradd -m -s /bin/bash agent
USER agent

# Read-only filesystem except /sandbox and /tmp
VOLUME ["/sandbox", "/tmp"]

# Drop all capabilities
# (Applied by OpenShell at runtime via --cap-drop=ALL)

# Seccomp profile
# (Applied by OpenShell at runtime via --security-opt)

# Network namespace isolation
# (Applied by OpenShell at runtime via --network=none + gateway proxy)

ENTRYPOINT ["/usr/bin/openclaw", "--sandbox-mode"]
```

The actual security enforcement happens at the OpenShell runtime level, not in the Dockerfile — the container definition sets the stage, but kernel-level restrictions are applied by the host's OpenShell process.
