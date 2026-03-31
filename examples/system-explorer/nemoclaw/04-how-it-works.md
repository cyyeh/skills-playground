## How It Works
<!-- level: intermediate -->
<!-- references:
- [How NemoClaw Works](https://docs.nvidia.com/nemoclaw/latest/about/how-it-works.html) | official-docs
- [Network Policies Reference](https://docs.nvidia.com/nemoclaw/latest/reference/network-policies.html) | official-docs
- [Inference Profiles Reference](https://docs.nvidia.com/nemoclaw/latest/reference/inference-profiles.html) | official-docs
-->

### Sandbox Isolation

NemoClaw achieves sandbox isolation through three complementary Linux kernel mechanisms, layered together to create defense in depth -- like a bank vault that uses a combination lock, a key lock, and biometric scanning rather than relying on any single mechanism.

**Landlock** restricts filesystem access at the kernel level. The sandbox permits read-write access only to `/sandbox` (the agent's working directory) and `/tmp`, while mounting all system paths as read-only. Unlike traditional Unix permissions, Landlock policies cannot be overridden by processes inside the sandbox, even if they somehow obtain root privileges.

**Seccomp** (Secure Computing Mode) filters system calls available to processes inside the sandbox. NemoClaw's seccomp profile blocks system calls that could be used to escape the container or modify the host system, such as `mount`, `ptrace`, and `reboot`. This prevents the agent from using kernel interfaces to circumvent the filesystem or network restrictions.

**Network namespaces** isolate the sandbox's network stack entirely from the host. The agent cannot see host network interfaces, bind to host ports, or enumerate host connections. All network traffic must pass through the OpenShell gateway, which acts as the sole controlled exit point.

### Blueprint Lifecycle

When an operator runs `nemoclaw onboard`, the system executes a five-stage pipeline that transforms a declarative blueprint into a running sandbox -- like a construction process that goes from blueprints to building inspection.

**Stage 1 -- Resolve**: The CLI fetches the blueprint artifact and resolves version constraints. If the operator specified a version range, the resolver picks the highest compatible version. The resolution result includes the exact version number and expected content digest.

**Stage 2 -- Verify**: The downloaded artifact's digest is checked against the expected value. If the digest does not match, the process halts immediately. This step ensures that a blueprint cannot be silently modified after approval -- like verifying a wax seal on a letter before reading it.

**Stage 3 -- Plan**: The blueprint runtime compares the desired state (defined in `blueprint.yaml` and `openclaw-sandbox.yaml`) against the current state of OpenShell resources. It produces a diff of resources to create, modify, or delete, similar to how `terraform plan` works.

**Stage 4 -- Apply**: The plan is executed by calling OpenShell CLI commands to create the sandbox container, configure the gateway, set up inference routing, and apply network policies.

**Stage 5 -- Status**: The system verifies that all resources were created successfully and reports their state. If any resource failed to initialize, the operator sees the failure immediately rather than discovering it later during agent operation.

### Inference Routing Pipeline

Inference routing is how NemoClaw keeps API credentials out of the sandbox while still letting the agent call LLM providers. The mechanism works through a series of request transformations -- like a mail forwarding service that rewrites addresses but preserves the letter inside.

1. The agent issues an API call to `inference.local`, a hostname that resolves only inside the sandbox's network namespace.
2. The OpenShell gateway intercepts this request at the namespace boundary.
3. The gateway inspects the request to determine which inference provider should handle it, based on the model identifier in the request and the provider configuration set during onboarding.
4. The gateway injects the real API credentials (stored on the host, never inside the sandbox) into the request headers.
5. The request is forwarded to the actual provider endpoint (e.g., `integrate.api.nvidia.com` for NVIDIA Endpoints, `api.openai.com` for OpenAI).
6. The provider's response returns through the gateway, which strips any metadata that could leak host-side configuration, and delivers it back to the agent via the `inference.local` endpoint.

This pipeline is transparent to the agent -- OpenClaw does not need any modifications to work with NemoClaw's inference routing because the local endpoint is OpenAI-compatible.

### Network Policy Enforcement

Network policy enforcement operates as a real-time packet filter at the OpenShell gateway -- like a customs checkpoint that inspects every outbound shipment against a manifest of approved destinations.

The policy file (`openclaw-sandbox.yaml`) defines allowed endpoints as a list of domain-method-port tuples. When the agent (or any process in the sandbox) attempts an outbound connection:

1. The gateway resolves the target hostname and checks it against the allowlist.
2. If the destination, HTTP method, and port match a policy entry, the connection proceeds.
3. If no match is found, the connection is blocked and logged.
4. The blocked request is surfaced in the OpenShell TUI (`openshell term`) for operator review.
5. The operator can approve the request, which adds a session-level policy entry, or deny it.

Static policy changes (editing the YAML file) require re-running `nemoclaw onboard` to take effect. Dynamic updates can be applied to running sandboxes using `openshell policy set <policy-file>` without requiring a restart.

### Provider Validation

During onboarding, NemoClaw validates that the selected inference provider is functional before creating the sandbox. The validation strategy differs by provider type because providers have inconsistent API surfaces:

- **OpenAI-compatible providers**: NemoClaw tests the `/responses` endpoint first, then falls back to `/chat/completions`.
- **Anthropic-compatible providers**: NemoClaw tests the `/v1/messages` endpoint.
- **NVIDIA manual entry**: NemoClaw validates against the NVIDIA models endpoint to confirm the model ID is valid.
- **Custom endpoints**: NemoClaw sends an actual inference request rather than checking a `/models` endpoint, because many proxy servers do not expose reliable model listing endpoints.

This validation prevents the frustrating scenario where an operator completes the full onboarding process only to discover that the inference provider is misconfigured.

### Credential Sanitization

NemoClaw implements credential stripping at multiple levels to prevent accidental exposure. When state is persisted or transmitted, the system scrubs known credential patterns from configuration objects, environment variables, and log output. This functions as a safety net behind the primary defense (host-side credential storage) -- like having both a fireproof safe and a sprinkler system, where either alone would reduce risk, but together they provide strong protection.

### Performance Characteristics

NemoClaw adds latency at two points: inference routing (the extra hop through the OpenShell gateway) and network policy checking (every outbound connection is evaluated against the allowlist). In practice, the inference routing overhead is small relative to the LLM inference time itself, which typically measures in seconds. The network policy check is a local operation with negligible latency. The primary performance cost is the sandbox container's disk footprint: the base image is approximately 2.4 GB compressed, which affects initial setup time but not runtime performance.
