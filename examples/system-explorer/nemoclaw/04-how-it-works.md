## How It Works
<!-- level: intermediate -->
<!-- references:
- [NemoClaw Architecture](https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html) | official-docs
- [NemoClaw GitHub README](https://github.com/NVIDIA/NemoClaw/blob/main/README.md) | github
- [OpenClaw Agent Tools](https://docs.openclaw.ai/plugins/agent-tools) | official-docs
- [NemoClaw Developer Guide](https://docs.nvidia.com/nemoclaw/latest/index.html) | official-docs
-->

This section walks through NemoClaw's operation end-to-end: from installation and first launch, through a complete tool-calling request, to ongoing monitoring and policy management.

### Step 1: Installation and Onboarding

NemoClaw installs via a single command:

```bash
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash
```

The install script:
1. Checks system requirements (Ubuntu 22.04+, 4 vCPU, 8 GB RAM, 20 GB disk)
2. Installs Node.js 22.16+ if not present
3. Downloads the NemoClaw CLI plugin and OpenShell runtime
4. Launches an interactive onboarding wizard

The wizard guides the operator through:
- **Inference provider selection:** NVIDIA Endpoints (default), local Ollama, or custom provider
- **API credential configuration:** Stored in `~/.nemoclaw/credentials.json` on the host (never in the sandbox)
- **Network policy review:** Preview the default deny-all policy and optionally pre-approve domains
- **Sandbox image download:** Pulls the OpenClaw container (~2.4 GB compressed)

### Step 2: Sandbox Launch

When the operator runs `nemoclaw launch`, the Blueprint lifecycle executes:

```
Resolve → Verify → Plan → Apply → Status
```

**Resolve:** The CLI locates the blueprint artifact from the OCI registry and checks version compatibility. Local caching avoids repeated downloads.

**Verify:** The artifact's digest is validated to detect tampering. If the digest doesn't match, the launch aborts.

**Plan:** The blueprint runner compares the desired sandbox state (from `blueprint.yaml` and `openclaw-sandbox.yaml`) against the current host state and calculates the required changes.

**Apply:** OpenShell CLI commands execute to:
- Create a network namespace with no default routes
- Launch the container with Landlock filesystem restrictions
- Apply seccomp syscall filters
- Drop all unnecessary Linux capabilities
- Configure the inference gateway endpoint
- Start the Policy Engine as a separate process

**Status:** The runner reports the sandbox's health, including active policies, inference provider, and resource usage.

### Step 3: Agent Interaction

Users communicate with the agent through:

- **Terminal UI:** `openclaw tui` — a rich terminal interface
- **CLI command:** `openclaw agent --agent main --local -m "message" --session-id test`
- **Messaging bridges:** Telegram, Discord, Slack, or WhatsApp relay messages into the sandbox via SSH, avoiding direct network exposure

### Step 4: Processing a Tool-Calling Request

Here is a complete walkthrough of a user requesting the agent to "check the status of our API endpoint at api.example.com":

**4a. Message Ingestion**
The user's message arrives at the sandbox via the messaging bridge. The message is delivered as structured data over SSH — the agent has no direct network socket to the messaging service.

**4b. Planning**
OpenClaw's planner evaluates the request. It determines that:
- The user wants an HTTP health check
- This requires network access to `api.example.com`
- An appropriate tool is the HTTP request tool

**4c. Tool Selection**
The planner queries the Tool Registry for available tools. Tools are registered via the plugin API:

```typescript
api.registerTool({
  name: "http_request",
  description: "Make an HTTP request to a specified URL",
  parameters: Type.Object({
    url: Type.String({ description: "The URL to request" }),
    method: Type.String({ enum: ["GET", "POST", "PUT", "DELETE"] }),
    headers: Type.Optional(Type.Record(Type.String(), Type.String())),
  }),
  async execute(_id, params) {
    const response = await fetch(params.url, {
      method: params.method,
      headers: params.headers,
    });
    return {
      content: [{ type: "text", text: JSON.stringify({
        status: response.status,
        body: await response.text(),
      })}],
    };
  },
});
```

The agent selects `http_request` with `url: "https://api.example.com/health"` and `method: "GET"`.

**4d. Network Policy Evaluation**
Before the HTTP request executes, the Rust Policy Engine intercepts the outbound connection:

1. Extracts the destination: `api.example.com:443`
2. Performs DNS resolution and IP validation (SSRF protection)
3. Checks the YAML policy file:

```yaml
# openclaw-sandbox.yaml (excerpt)
network:
  egress:
    default: deny
    allow:
      - host: "api.nvidia.com"
        ports: [443]
      - host: "api.example.com"
        ports: [443]
        methods: ["GET", "HEAD"]
```

4. If the destination is allowlisted: the connection proceeds
5. If the destination is NOT allowlisted: the connection is blocked and an alert appears in the operator's TUI

**4e. Operator Approval (if needed)**
When the Policy Engine blocks an unknown destination, the operator sees a real-time prompt in the OpenShell terminal:

```
[POLICY] Agent requests access to: api.unknown.com:443
         Action: GET /status
         Reason: User requested API health check
         [A]pprove  [D]eny  [A]pprove+Remember
```

Choosing "Approve+Remember" adds the domain to the running policy (and optionally persists it to the YAML file).

**4f. Tool Execution**
With network access approved, the tool's `execute` function runs inside the sandbox. The HTTP request goes through the OpenShell gateway, which:
- Validates the connection against the (now-updated) policy
- Logs the request details (URL, method, timestamp, response code)
- Proxies the connection to the destination

**4g. Inference for Response Synthesis**
The agent now needs to synthesize a response from the tool's output. This triggers an inference request:

1. The Privacy Router examines the prompt content
2. It classifies the data: API status responses typically contain non-sensitive operational data
3. It routes to the configured cloud provider (or local Nemotron if classified as sensitive)
4. The Inference Gateway injects the provider's API credentials and proxies the request
5. The LLM generates a natural language summary of the API status

**4h. Response Delivery**
The synthesized response travels back through the messaging bridge to the user:

```
The API at api.example.com is healthy. The /health endpoint returned 
HTTP 200 with response time of 142ms. All services report operational 
status.
```

### Step 5: Ongoing Monitoring

Operators can monitor the sandbox in real-time:

- **`nemoclaw status`** — Shows sandbox health, active policies, resource usage
- **`nemoclaw logs`** — Streams audit logs including every tool call, network request, and inference routing decision
- **`openshell term`** — Opens the TUI for real-time policy management and approval workflows

### Step 6: Policy Hot-Reload

Network and filesystem policies can be updated without restarting the sandbox:

1. Edit `openclaw-sandbox.yaml` to add new allowlisted domains or restrict existing ones
2. The Policy Engine detects the change and applies it immediately
3. No sandbox restart required — the agent continues operating with updated constraints

This enables progressive trust: start with minimal permissions and expand them as the agent proves reliable.

### Step 7: Workspace Persistence

The sandbox provides persistent workspace storage:
- Agent state, conversation history, and files are stored in `/sandbox`
- Backup and restore operations are available via `nemoclaw backup` and `nemoclaw restore`
- Workspace data survives sandbox restarts and blueprint updates
