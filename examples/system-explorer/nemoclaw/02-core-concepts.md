## Core Concepts
<!-- level: beginner -->
<!-- references:
- [NemoClaw Architecture Reference](https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html) | official-docs
- [How NemoClaw Works](https://docs.nvidia.com/nemoclaw/latest/about/how-it-works.html) | official-docs
- [Network Policies Reference](https://docs.nvidia.com/nemoclaw/latest/reference/network-policies.html) | official-docs
-->

### Sandbox

A **sandbox** is an isolated container environment where the OpenClaw agent runs -- like a sealed clean room in a laboratory. The agent can work freely inside the room, but every entrance and exit is monitored and controlled. NemoClaw sandboxes enforce filesystem boundaries (the agent can only write to `/sandbox` and `/tmp`) and network restrictions using Linux kernel mechanisms including [Landlock](https://docs.kernel.org/security/landlock.html), seccomp, and network namespace isolation. The sandbox denies everything by default and only permits what is explicitly allowed. This matters because autonomous agents executing arbitrary code are inherently risky; the sandbox is the first line of defense against unintended side effects.

### Blueprint

A **blueprint** is a versioned artifact that defines how a sandbox should be configured -- like an architectural plan for a building that specifies every room, door, and security system before construction begins. Blueprints contain a manifest file (`blueprint.yaml`) and policy definitions (`openclaw-sandbox.yaml`). The [blueprint lifecycle](https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html) follows five stages: resolve version constraints, verify artifact digest, plan required resource changes, apply those changes, and report system state. Blueprints ensure that sandbox deployments are reproducible and tamper-evident.

### Network Policy

A **network policy** is a declarative YAML file that defines exactly which external endpoints the agent is permitted to contact -- like a whitelist for a corporate firewall. NemoClaw operates on a [deny-by-default model](https://docs.nvidia.com/nemoclaw/latest/reference/network-policies.html): if an endpoint is not listed in the policy, the agent cannot reach it. Policies specify allowed domains, ports (all connections enforce TLS on port 443), and even HTTP methods (for example, documentation endpoints may allow only GET requests). This gives operators precise control over what data the agent can send or receive.

### Inference Routing

**Inference routing** is the mechanism that directs the agent's LLM API calls through a controlled path rather than letting the agent contact model providers directly -- like routing all phone calls through a corporate switchboard instead of letting employees dial external numbers from their desks. The agent communicates with a local endpoint (`inference.local`) inside the sandbox, while [OpenShell](https://docs.nvidia.com/nemoclaw/latest/about/overview.html) on the host manages actual credentials and upstream connections. This design keeps API keys out of the sandbox entirely, preventing credential leakage even if the agent is compromised.

### OpenShell

**OpenShell** is the NVIDIA runtime that NemoClaw depends on, part of the broader [NVIDIA Agent Toolkit](https://docs.nvidia.com/nemoclaw/latest/about/overview.html) -- like the operating system on which NemoClaw applications run. OpenShell provides the gateway that intercepts and routes inference requests, the kernel-level isolation mechanisms for sandboxing, and the TUI (terminal user interface) for monitoring and approving network requests in real time. NemoClaw is essentially a purpose-built configuration layer on top of OpenShell, specialized for running OpenClaw securely.

### Approval Workflow

The **approval workflow** is the process by which an operator reviews and permits network requests that the agent attempts to make to unlisted endpoints -- like a security guard checking packages at the loading dock. When the agent tries to reach a host not in the network policy, OpenShell blocks the request and surfaces it in the [TUI](https://docs.nvidia.com/nemoclaw/latest/reference/network-policies.html) for the operator to approve or deny. Approved requests can be added to the session-level policy so the operator does not have to approve the same endpoint repeatedly. This matters because it provides a human-in-the-loop safety net for unexpected agent behavior.

### Inference Provider

An **inference provider** is a backend that serves LLM responses to the agent -- like choosing which telephone company handles your calls. NemoClaw supports six categories: [NVIDIA Endpoints](https://build.nvidia.com/nemoclaw) (including Nemotron), OpenAI, Anthropic, Google Gemini, custom OpenAI-compatible proxies, and local self-hosted runtimes (Ollama, NVIDIA NIM, vLLM). The system validates each provider during onboarding and routes requests through the OpenShell gateway, so the agent never sees raw API credentials regardless of which provider is selected.

### How They Fit Together

NemoClaw's concepts form a layered security model. The **blueprint** defines the desired state of a deployment. That blueprint is applied to create a **sandbox** -- an isolated environment where the OpenClaw agent lives. Inside the sandbox, the agent's outbound network traffic is governed by the **network policy**, and any requests to unlisted destinations trigger the **approval workflow** for human review. The agent's model calls are handled by **inference routing**, which channels them through **OpenShell** to the configured **inference provider** without exposing credentials. The result is a system where an autonomous agent can operate continuously while every boundary -- filesystem, network, and credentials -- is explicitly controlled.
