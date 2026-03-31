## Common Q&A
<!-- level: all -->
<!-- references:
- [NemoClaw GitHub Issues](https://github.com/NVIDIA/NemoClaw/issues) | github
- [NemoClaw Developer Guide](https://docs.nvidia.com/nemoclaw/latest/index.html) | official-docs
- [NVIDIA Developer Forums](https://forums.developer.nvidia.com/t/total-nightmare-nemoclaw-over-paperclip-over-openclaw-over-vllm-over-dokers-over-llm-flavours-over-linux/363682) | forum
- [NemoClaw FAQ](https://github.com/NVIDIA/NemoClaw/blob/main/README.md) | github
-->

### Q1: Is NemoClaw a model, a framework, or a runtime?

**NemoClaw is a runtime and security layer**, not a model or a full agent framework. It wraps the existing OpenClaw agent framework with NVIDIA's OpenShell runtime to provide sandboxing, policy enforcement, privacy routing, and managed inference. Think of it as the secure operating environment that an agent runs inside, rather than the agent itself.

---

### Q2: Do I need NVIDIA GPUs to use NemoClaw?

**No.** NemoClaw itself requires no GPUs — its minimum requirement is just 4 vCPU, 8 GB RAM, and 20 GB disk. GPUs are only needed if you want to run Nemotron models locally for privacy routing. Without local GPUs, you can route all inference to cloud providers (NVIDIA Endpoints, OpenAI, Anthropic) through the NemoClaw gateway. Of course, local models require appropriate GPU hardware (the full Nemotron 3 Super 120B works best on DGX-class hardware, while the Nano 4B variant can run on consumer RTX cards).

---

### Q3: Is NemoClaw production-ready?

**Not yet.** As of March 2026, NemoClaw is labeled as alpha software in early preview. The official documentation explicitly states: "APIs, configuration schemas, and runtime behavior are subject to breaking changes between releases. Do not use this software in production environments." The architecture and security model are sound, but the project has not undergone independent security audits, and the API surface is still stabilizing.

---

### Q4: How does NemoClaw differ from just running OpenClaw in a Docker container?

The difference is significant. A standard Docker container provides **process isolation** but does not enforce fine-grained network policies, filesystem access controls, or managed inference routing. NemoClaw adds:
- **Landlock** filesystem restrictions (more granular than Docker volume mounts)
- **seccomp** syscall filtering (blocking dangerous kernel operations)
- **Network namespaces** with deny-by-default egress (standard containers have full outbound access)
- **Out-of-process policy enforcement** (a Rust engine the agent cannot tamper with)
- **Privacy routing** for inference (standard Docker has no concept of this)
- **Credential isolation** (API keys never enter the container)

Standard Docker provides a sandbox; NemoClaw provides a hardened, policy-governed, auditable sandbox.

---

### Q5: Can I use NemoClaw with models other than Nemotron?

**Yes.** NemoClaw supports any inference provider through three mechanisms:
1. **NVIDIA Endpoints** for NVIDIA-hosted models (default: Nemotron 3 Super)
2. **Local Ollama** for any model available through Ollama (Llama, Mistral, Qwen, etc.)
3. **Custom OpenAI-compatible providers** for cloud APIs (OpenAI GPT-4o, Anthropic Claude, Google Gemini, etc.)

The Privacy Router decides which provider to use per-request based on data sensitivity. You can configure multiple providers and have sensitive queries routed to a local model while non-sensitive queries go to a more capable cloud model.

---

### Q6: How much latency does NemoClaw add?

The security pipeline adds approximately **300ms to the first request** in a session (sandbox initialization, policy engine startup, and initial route calculation) and **under 100ms for subsequent requests** (due to policy caching and persistent connections). The inference routing itself adds minimal overhead — it is primarily DNS resolution and policy lookup. In practice, the LLM inference time (typically 1-10 seconds) dominates total latency, making NemoClaw's overhead negligible.

---

### Q7: Can the agent bypass NemoClaw's security controls?

**By design, no.** This is the key architectural innovation. Unlike prompt-level guardrails (which can be bypassed through prompt injection), NemoClaw's security is enforced at the Linux kernel level by a separate process:
- **Landlock** prevents filesystem access regardless of what the agent attempts
- **seccomp** blocks system calls before they reach the kernel
- **Network namespaces** mean the agent has no network interface to manipulate
- **The Policy Engine** runs in its own process — the agent cannot modify it

Even if an attacker achieves arbitrary code execution inside the sandbox, they are still constrained by these kernel-level restrictions. However, no security system is perfect — NemoClaw has not yet been independently audited, and novel kernel exploits could theoretically bypass these controls.

---

### Q8: How does NemoClaw handle multi-agent scenarios?

OpenClaw supports **supervisor-worker patterns** where a supervisor agent delegates tasks to specialized worker agents. In NemoClaw, each agent can run in its own sandbox with its own policy:
- A supervisor agent might have network access to Slack and Jira
- A code-writing worker agent might only have access to GitHub
- A data analysis worker might only have access to the internal database

This provides **per-agent blast radius limitation** — a compromised worker agent can only affect the systems it was explicitly granted access to.

---

### Q9: What operating systems does NemoClaw support?

NemoClaw primarily targets **Ubuntu 22.04 LTS or later** on Linux, as it relies on Linux kernel security features (Landlock, seccomp, network namespaces) that are not available on other operating systems. For **macOS**, NemoClaw works via Colima or Docker Desktop, though the kernel-level security is provided by the container runtime's Linux VM rather than the host OS. For **Windows**, Docker Desktop with WSL is supported with the same caveat. Full security guarantees require a native Linux kernel.

---

### Q10: How do I monitor what the agent is doing?

NemoClaw provides three monitoring mechanisms:
1. **`nemoclaw logs`** — Streams structured audit logs including tool calls, network requests, and inference routing decisions
2. **`nemoclaw status`** — Shows sandbox health, active policies, resource usage, and provider connectivity
3. **`openshell term`** — Opens a TUI (terminal UI) for real-time interaction: viewing pending policy approval requests, inspecting current connections, and managing sandbox state

All audit data is structured JSON, making it straightforward to pipe into enterprise logging systems (ELK stack, Splunk, Datadog) for centralized monitoring and alerting.
