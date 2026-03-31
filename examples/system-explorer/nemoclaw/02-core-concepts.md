## Core Concepts
<!-- level: beginner -->
<!-- references:
- [NemoClaw Overview](https://docs.nvidia.com/nemoclaw/latest/about/overview.html) | official-docs
- [How NemoClaw Works](https://docs.nvidia.com/nemoclaw/latest/about/how-it-works.html) | official-docs
- [OpenShell Technical Blog](https://developer.nvidia.com/blog/run-autonomous-self-evolving-agents-more-safely-with-nvidia-openshell/) | blog
-->

### The Sandbox

**Definition:** The sandbox is an isolated container environment where the OpenClaw agent lives and operates. It's created from a hardened Docker image (the "blueprint") with strict filesystem, network, and process restrictions applied from the first boot.

**Analogy:** Think of a bank vault with a teller inside. The teller (agent) can do useful work -- answer questions, process requests, write code -- but the vault walls (sandbox) physically prevent them from walking into the back office, accessing other vaults, or leaving the building without going through the controlled entrance. Even if the teller decided to misbehave, the vault constrains what's possible.

**Why it matters:** Traditional AI agent deployments rely on the agent "choosing" not to do harmful things, enforced via system prompts or in-agent guardrails. A sophisticated agent can potentially circumvent these. NemoClaw's sandbox enforces restrictions at the operating system level using Landlock (filesystem), seccomp (system calls), and network namespaces, making them physically impossible to bypass from inside the sandbox.

### The Blueprint

**Definition:** The blueprint is a versioned Python artifact that contains the complete recipe for creating a NemoClaw sandbox: the Dockerfile, security policies, network configurations, and inference setup. The CLI plugin resolves, verifies, and executes the blueprint as a subprocess.

**Analogy:** If the sandbox is a secure facility, the blueprint is the architectural plan and building code combined. It specifies exactly how the walls should be built, where the doors go, what locks to use, and what security systems to install. The blueprint has its own version number and release cycle, so security improvements ship independently from the CLI tool.

**Why it matters:** Separating the blueprint from the CLI keeps the user-facing tool small and stable while allowing the security-critical sandbox definition to evolve rapidly. When NVIDIA releases a new blueprint version, your sandbox gets updated security policies without requiring a CLI update.

### The Privacy Router

**Definition:** The privacy router is a component of OpenShell that intercepts every inference API call made by the agent and routes it to either a local model (like NVIDIA Nemotron running on your hardware) or a cloud-based model, based on policies you define rather than the agent's preferences.

**Analogy:** Imagine a corporate mail room that inspects every outgoing letter. Sensitive documents get hand-delivered by a trusted courier (local inference), while routine correspondence goes through regular mail (cloud API). The mail room makes the routing decision based on company policy -- the letter writer has no say in which route their message takes.

**Why it matters:** Agents frequently need to call language models for reasoning, planning, and generation. Without a privacy router, every prompt and context window gets sent to a cloud API, potentially leaking sensitive data. The privacy router lets you keep sensitive inference local while still accessing powerful frontier models for non-sensitive tasks.

### Policy Enforcement Layers

**Definition:** NemoClaw enforces security through four distinct layers, each operating at a different level of the system: network policies (controlling outbound connections), filesystem policies (restricting file access), process policies (preventing privilege escalation), and inference policies (routing model API calls).

**Analogy:** Think of airport security with multiple checkpoints. The perimeter fence (network policy) controls who enters the airport. The boarding pass check (filesystem policy) restricts which areas you can access. The security screening (process policy) prevents you from carrying prohibited items. The gate agent (inference policy) verifies you're boarding the right plane. Each layer catches different threats, and you must pass all of them.

**Why it matters:** No single security mechanism catches everything. Network restrictions can't stop the agent from reading sensitive files inside the sandbox. Filesystem restrictions can't stop unauthorized API calls. By layering four independent enforcement mechanisms, NemoClaw creates defense in depth -- compromising one layer doesn't compromise the others.

### OpenShell Runtime

**Definition:** OpenShell is the NVIDIA Agent Toolkit runtime that sits between the agent and the host infrastructure. It provides the sandbox container, the policy engine, the privacy router, and the credential management system. NemoClaw is essentially a pre-configured deployment of OpenShell tailored for OpenClaw.

**Analogy:** If NemoClaw is a turnkey security system for your home, OpenShell is the underlying smart-home platform it's built on. OpenShell provides the cameras, locks, alarm sensors, and control panel. NemoClaw configures them specifically for the OpenClaw use case -- which doors to lock, which cameras to activate, which alarms to set.

**Why it matters:** OpenShell is a general-purpose agent security runtime that can work with multiple agent types (OpenClaw, Claude Code, Cursor, Codex). NemoClaw's value is in the opinionated, pre-configured deployment of OpenShell that eliminates the need to write security policies from scratch.

### Inference Providers

**Definition:** Inference providers are the backends that actually run language model inference when the agent makes an API call. NemoClaw supports NVIDIA Endpoints (cloud), OpenAI, Anthropic, Google Gemini, and local providers like Ollama and vLLM.

**Analogy:** Think of inference providers as different phone carriers. Your phone (agent) dials a number (sends a prompt), and the carrier (provider) connects the call (runs inference). NemoClaw is the corporate IT department that decides which carrier handles which calls based on cost, privacy, and capability policies.

**Why it matters:** Different tasks have different requirements. Sensitive code reviews might need local inference for privacy, while complex architectural planning might benefit from a frontier cloud model. NemoClaw lets you define which provider handles which requests, and it manages the credentials so the agent never sees API keys directly.

### How They Fit Together

When you run `nemoclaw onboard`, the CLI plugin downloads and verifies the blueprint, which creates an OpenShell sandbox pre-configured for OpenClaw. Inside the sandbox, the agent runs with four enforcement layers active: the filesystem is restricted to `/sandbox` and `/tmp`, network egress is blocked except for an operator-defined allowlist, dangerous system calls are filtered by seccomp, and all inference API calls are intercepted by the privacy router and routed through OpenShell's gateway to configured providers. The agent operates freely within these boundaries -- it can write files, execute code, and reason about tasks -- but it cannot access data outside the sandbox, make unapproved network connections, escalate privileges, or choose where its inference calls go. The operator controls all of this through YAML-based policy files that can be updated at runtime without restarting the sandbox.
