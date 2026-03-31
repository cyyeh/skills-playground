## Core Concepts
<!-- level: beginner -->
<!-- references:
- [NemoClaw Architecture Reference](https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html) | official-docs
- [OpenClaw Agent Tools](https://docs.openclaw.ai/plugins/agent-tools) | official-docs
- [NVIDIA NemoClaw GitHub README](https://github.com/NVIDIA/NemoClaw/blob/main/README.md) | github
- [NemoClaw Enterprise Guide](https://www.ai.cc/blogs/nvidia-nemoclaw-open-source-ai-agent-2026-guide/) | article
-->

### OpenClaw (The Agent Framework)

**Definition:** OpenClaw is the open-source AI assistant framework that NemoClaw wraps and secures. It provides the core agent capabilities — multi-step task execution, tool calling, code generation, and persistent operation across messaging channels like Telegram, Discord, Slack, and the terminal.

**Analogy:** If NemoClaw is the security perimeter of a building, OpenClaw is the worker inside who actually does the job. OpenClaw handles reasoning, planning, and execution; NemoClaw ensures that worker stays within approved boundaries.

**Why it matters:** Without OpenClaw, there is no agent. NemoClaw does not replace OpenClaw's capabilities — it governs them. Understanding this separation is essential: OpenClaw decides *what* to do, NemoClaw controls *whether it is allowed*.

---

### OpenShell (The Secure Runtime)

**Definition:** NVIDIA OpenShell is a kernel-level sandbox runtime, part of the NVIDIA Agent Toolkit, that provides the isolation and policy enforcement layer for NemoClaw. It enforces filesystem restrictions, network policies, and process limits using Linux kernel security features including Landlock, seccomp, and network namespaces.

**Analogy:** OpenShell is like a high-security clean room. The agent can work freely inside the room, but cannot touch anything outside it — the walls are enforced by the operating system kernel itself, not by the agent's own good behavior.

**Why it matters:** Traditional AI security relies on prompt-level instructions ("don't access this file") which can be bypassed through prompt injection. OpenShell enforces restrictions at the OS level, creating a trust boundary that the agent cannot circumvent regardless of how its prompts are manipulated.

---

### Sandbox (The Isolated Container)

**Definition:** The sandbox is the isolated execution environment where the OpenClaw agent runs. It is a hardened container image (`ghcr.io/nvidia/openshell-community/sandboxes/openclaw`) with restricted filesystem access (`/sandbox` and `/tmp` for read-write, system paths read-only), no direct network access, and limited process capabilities.

**Analogy:** Think of a sandbox like a virtual office assigned to a contractor. They can use the desk and supplies provided, but cannot wander the building, cannot bring in outside materials without security approval, and every entry and exit is logged.

**Why it matters:** The sandbox is the fundamental security primitive. All agent code runs inside it, all tool executions happen within it, and all external communication must pass through the OpenShell gateway. This defense-in-depth approach means a single vulnerability cannot compromise the host system.

---

### Privacy Router

**Definition:** The Privacy Router inspects each inference request and classifies its data sensitivity. Requests containing PII, proprietary code, or sensitive financial data are routed to local Nemotron models that run on-premises. Non-sensitive queries can be routed to cloud providers (OpenAI, Anthropic, Google) for higher capability or lower cost.

**Analogy:** The Privacy Router acts like a mail sorter in a classified facility. Confidential documents go through the internal courier; routine correspondence can use regular postal service. The classification rules are set by the organization, not by the mail itself.

**Why it matters:** This solves a fundamental enterprise tension: organizations want the best available AI models but cannot send sensitive data to external APIs. The Privacy Router provides automatic, policy-driven routing that balances capability with data sovereignty.

---

### Network Policy Engine

**Definition:** A Rust-based policy engine that intercepts every outbound network connection from the sandbox and validates it against declarative YAML rules. The default policy is deny-all — the agent cannot reach any external endpoint unless it is explicitly allowlisted in the `openclaw-sandbox.yaml` configuration file.

**Analogy:** Imagine a firewall that starts with "block everything" and only opens doors to specific addresses that have been pre-approved. Every attempted connection is logged, and unknown destinations trigger a real-time alert for the operator to approve or deny.

**Why it matters:** Autonomous agents that can browse the web and call APIs pose exfiltration risks. The deny-by-default model ensures that even if an agent is instructed to send data to an unauthorized endpoint, the connection is blocked at the kernel level before any data leaves.

---

### Blueprint (The Deployment Artifact)

**Definition:** The Blueprint is a versioned Python artifact that orchestrates the sandbox creation, security policy application, and inference setup. It follows a five-stage lifecycle: Resolve (locate artifact), Verify (check digest integrity), Plan (determine required changes), Apply (execute OpenShell commands), and Status (report current state).

**Analogy:** A Blueprint is like an infrastructure-as-code template (think Terraform or Helm chart) specifically designed for agent deployments. It declaratively specifies what the sandbox looks like, what policies apply, and how inference is routed.

**Why it matters:** Blueprints make deployments reproducible and auditable. Instead of manually configuring each sandbox, operators define the desired state in a versioned artifact, and the blueprint runner ensures the actual environment matches.

---

### Tool Registry and Agent Tools

**Definition:** Tools are typed functions that the LLM can call to interact with external systems. In OpenClaw, tools are registered via the plugin API using `api.registerTool()` with a name, description, typed parameter schema (using TypeBox), and an async execute function. NemoClaw governs which tools the agent is allowed to use through its policy layer.

**Analogy:** Tools are like the instruments on a surgeon's tray — each one has a specific purpose and defined interface. The tool registry is the tray itself, listing what is available. NemoClaw acts as the operating room protocol that determines which instruments are approved for this particular procedure.

**Why it matters:** Tool calling is what makes agents useful beyond text generation. The ability to query databases, call APIs, execute code, and manage files transforms an LLM from a chatbot into an autonomous worker. NemoClaw's governance ensures this power is exercised within approved boundaries.

---

### Inference Routing (Managed Inference)

**Definition:** All inference requests from the agent are routed through the OpenShell gateway to the configured provider. The agent never contacts inference endpoints directly and never holds API credentials. The gateway injects credentials and enforces policies at the boundary, keeping the sandbox credential-free.

**Analogy:** Like a corporate VPN that mediates all internet access — employees access external services through the company gateway, which handles authentication, logging, and policy enforcement, rather than connecting directly from their workstations.

**Why it matters:** Credential-free sandboxes eliminate an entire class of attack vectors. If the agent's sandbox is compromised, no API keys or authentication tokens are exposed because they were never there to begin with.

---

### How They Fit Together

The NemoClaw stack operates as a layered architecture:

1. **The user** sends a message via terminal, Telegram, Discord, or Slack
2. **OpenClaw** (the agent) receives the message and plans a response, which may involve calling tools or generating code
3. **The Tool Registry** provides available tools with typed schemas; the agent selects and invokes them
4. **The Sandbox** (OpenShell) constrains all execution — filesystem, network, and processes are restricted by kernel-level policies
5. **The Network Policy Engine** evaluates any outbound connection against the YAML policy; denied connections are blocked and logged
6. **The Privacy Router** classifies inference requests by sensitivity and routes them to local Nemotron models or cloud providers
7. **The Inference Gateway** proxies the model call, injecting credentials and applying rate limits
8. **The Blueprint** manages the entire deployment lifecycle, ensuring reproducible and auditable configurations
9. **Audit logs** capture every action — tool calls, network requests, inference routing decisions — for compliance review
