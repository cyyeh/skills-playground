## Trade-offs & Limitations
<!-- level: intermediate -->
<!-- references:
- [NemoClaw vs OpenClaw Comparison](https://medium.com/@aizarashid17/nemoclaw-vs-openclaw-does-nemoclaw-replace-openclaw-f26f9757645d) | blog
- [OpenClaw Alternatives for Enterprise Security](https://fountaincity.tech/resources/blog/openclaw-alternatives-enterprise-security-comparison/) | blog
- [NemoClaw GitHub Repository](https://github.com/NVIDIA/NemoClaw) | github
-->

### Strengths

**Defense-in-depth security model.** NemoClaw layers three kernel-level isolation mechanisms (Landlock, seccomp, network namespaces) with host-side credential storage and a deny-by-default network policy. No single mechanism is the sole line of defense. This is a genuinely thoughtful security architecture, not a checkbox exercise -- like a building that uses both fireproof construction materials and a sprinkler system rather than relying on either alone.

**Host-side credential isolation.** API keys never enter the sandbox. The agent sees only `inference.local`, while the OpenShell gateway injects real credentials during request forwarding. This is perhaps NemoClaw's strongest architectural decision: even a fully compromised agent cannot exfiltrate model provider credentials because they do not exist in its environment.

**Wrapping over forking.** By running an unmodified OpenClaw inside the sandbox rather than maintaining a security fork, NemoClaw can absorb upstream OpenClaw updates without merge conflicts. This makes the project sustainable long-term and avoids the common open-source pattern where security forks fall behind their parent projects.

**Human-in-the-loop approval workflow.** The real-time network request approval system via the OpenShell TUI provides a practical mechanism for incremental trust. Operators can start with a minimal policy, observe what the agent tries to reach, and selectively grant access -- like gradually extending a new employee's building access as they demonstrate trustworthiness.

**Provider flexibility.** Supporting six inference provider categories (NVIDIA, OpenAI, Anthropic, Gemini, custom OpenAI-compatible, local runtimes) means NemoClaw is not a lock-in tool despite being an NVIDIA project. Organizations can use their preferred model provider while still benefiting from the security stack.

### Limitations

**Alpha maturity.** NemoClaw was released on March 16, 2026, and has not yet reached a stable release. APIs, configuration schemas, and runtime behavior may change without notice. No organization has run it in production at scale, which means the real-world failure modes are not yet catalogued. Early adoption requires a tolerance for breakage.

**Linux-only kernel isolation.** The core security mechanisms (Landlock, seccomp, network namespaces) are Linux kernel features. macOS and Windows support relies on running Linux inside a VM (Docker Desktop, Colima, WSL), which adds a virtualization layer that increases complexity and reduces the directness of the security guarantees. Teams whose developers primarily use macOS will experience NemoClaw through an extra layer of abstraction.

**Coarse filesystem policy.** The agent can read-write everything under `/sandbox` and `/tmp`, with the rest of the filesystem read-only. There is no per-file or per-directory granularity within the writable zones. If an agent should have write access to some files in `/sandbox` but not others, you must structure your workspace layout to work around this limitation.

**Infrastructure weight.** NemoClaw requires Docker, the OpenShell runtime, and a ~2.4 GB sandbox image. For teams already using Docker, this is manageable. For teams without container infrastructure, the setup overhead is significant compared to running plain OpenClaw as a VS Code extension or CLI tool. The stack adds operational complexity that must be justified by the security requirements.

**No built-in multi-agent orchestration.** Despite some descriptions mentioning multi-agent capabilities, NemoClaw as shipped is focused on securing individual OpenClaw instances. Coordinating multiple agents that need to share context or delegate tasks to each other requires custom solutions on top of NemoClaw's sandboxing primitives.

### Alternatives Comparison

**Plain OpenClaw (without NemoClaw)** -- OpenClaw runs directly on the developer's machine with full filesystem and network access. It is simpler to set up, lower latency (no gateway hop), and works natively on macOS, Windows, and Linux. Choose OpenClaw alone when the threat model does not include autonomous agent behavior (e.g., interactive coding sessions where the human reviews every action) or when setup simplicity matters more than isolation guarantees. Choose NemoClaw when the agent runs unattended, processes sensitive code, or needs network egress controls.

**NanoClaw** -- A lightweight alternative focused on rapid deployment and code readability. NanoClaw prioritizes minimal overhead and a simple codebase over NemoClaw's comprehensive security stack. Choose NanoClaw when you need a fast, self-hosted coding agent without the infrastructure requirements of NemoClaw. Choose NemoClaw when security guarantees, credential isolation, and network policy controls are non-negotiable requirements.

**DIY Docker + reverse proxy** -- Building your own isolation layer using Docker's `--network=none` flag, a reverse proxy for API routing, and custom scripts for policy enforcement. This approach offers maximum flexibility and avoids the OpenShell dependency. Choose the DIY approach when you need custom isolation requirements that NemoClaw's prescribed model does not support or when you want to avoid NVIDIA's runtime dependencies. Choose NemoClaw when you want a pre-built, tested solution rather than investing engineering time in custom infrastructure.

### The Honest Take

NemoClaw addresses a real and growing problem: autonomous AI agents that can execute arbitrary code need stronger security boundaries than traditional development tools. Its architecture is sound -- host-side credentials, kernel-level isolation, deny-by-default networking -- and the wrapping-over-forking approach makes it sustainable. However, it is two weeks old at the time of this analysis, explicitly alpha, and requires a non-trivial infrastructure commitment (Docker + OpenShell + 2.4 GB image). Recommend it for teams that are already evaluating always-on AI agents and have the operational maturity to tolerate alpha-stage software. Do not recommend it for teams that just want a coding assistant for interactive use -- plain OpenClaw is simpler and sufficient for that scenario.
