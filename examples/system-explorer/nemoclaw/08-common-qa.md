## Common Q&A
<!-- level: all -->
<!-- references:
- [NemoClaw Troubleshooting](https://docs.nvidia.com/nemoclaw/latest/reference/troubleshooting.html) | official-docs
- [NemoClaw Architecture](https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html) | official-docs
- [NemoClaw Network Policies](https://docs.nvidia.com/nemoclaw/latest/reference/network-policies.html) | official-docs
-->

### Q: What happens if the agent is compromised via prompt injection -- can it escape the sandbox?

The sandbox is designed to contain even a worst-case scenario where an attacker achieves arbitrary code execution inside the container. The three-layer isolation (Landlock for filesystem, seccomp for syscalls, network namespaces for networking) is enforced at the Linux kernel level, not by the application. A compromised agent cannot mount new filesystems, trace other processes, or bypass network restrictions because the kernel blocks these operations before they execute. The most important practical consequence: API keys are stored on the host and injected by the OpenShell gateway during request forwarding, so even full sandbox compromise cannot exfiltrate credentials. That said, container escapes are not theoretically impossible -- they require kernel vulnerabilities, which is why defense in depth (all three mechanisms plus host-side credential storage) matters.

### Q: How does NemoClaw compare to just running OpenClaw in a Docker container with restricted networking?

A plain Docker container with `--network=none` plus a reverse proxy could approximate some of NemoClaw's functionality, but you would be reimplementing several things from scratch: the inference routing that keeps API keys host-side, the per-domain/per-method network policy engine, the real-time approval workflow for blocked requests, the blueprint versioning with digest verification, and the onboarding wizard that validates inference providers. NemoClaw packages these into a coherent stack. The trade-off is complexity: NemoClaw adds OpenShell as a dependency and prescribes a specific deployment model, while a DIY Docker approach gives you more flexibility at the cost of more work.

### Q: Can I run multiple sandboxed agents simultaneously?

Yes. Each sandbox is an independent container instance with its own name (RFC 1123 format), network namespace, and policy configuration. You can run `nemoclaw onboard` multiple times to create different sandboxes with different inference providers or network policies. The `nemoclaw list` command shows all registered sandboxes. The practical limit is host resources: each sandbox consumes memory and CPU, and if using local inference, the model runtime adds significant overhead.

### Q: What is the latency overhead of inference routing through OpenShell?

The routing adds one extra network hop (sandbox to OpenShell gateway to provider). For cloud inference providers, this overhead is typically negligible compared to the LLM inference time itself, which ranges from hundreds of milliseconds to several seconds. For local inference (Ollama, NIM), the hop is entirely local and adds sub-millisecond latency. The network policy check is a local table lookup and does not measurably affect latency. The most noticeable delay is during initial sandbox setup, where the 2.4 GB container image must be downloaded and extracted.

### Q: How do I grant the agent access to a new API without restarting the sandbox?

There are two approaches. For immediate, session-scoped access: wait for the agent to attempt the request, then approve it in the OpenShell TUI (`openshell term`). The approval applies for the current session only. For persistent access: use `openshell policy set <policy-file>` with an updated YAML file to modify the running sandbox's network policy without restart. For changes that should survive sandbox recreation, edit the policy YAML in the blueprint and re-onboard.

### Q: Is NemoClaw locked into NVIDIA hardware?

No. NemoClaw is hardware-agnostic at the agent layer. The sandbox runs on any Linux machine with Docker, regardless of GPU vendor. The NVIDIA-specific optimizations are in the inference layer: Nemotron models and NVIDIA NIM run best on NVIDIA GPUs. But you can use non-NVIDIA inference providers (OpenAI, Anthropic, Ollama with CPU-only models) on AMD or Intel hardware. The kernel-level isolation mechanisms (Landlock, seccomp, namespaces) are Linux kernel features, not NVIDIA-specific.

### Q: What happens to agent state if the host machine reboots?

The sandbox container persists across host reboots if Docker is configured to restart containers automatically (the default for most Docker installations). Agent state inside `/sandbox` is preserved in the container's filesystem layer. However, session-level policy approvals (granted via the TUI) are not persisted -- only static policy changes (written to the YAML file) survive restarts. NemoClaw's workspace documentation includes backup and restore procedures for the `/sandbox` directory.

### Q: Can I use NemoClaw with a model provider not in the supported list?

Yes, through the "Custom OpenAI-compatible" or "Custom Anthropic-compatible" provider options during onboarding. Any endpoint that speaks the OpenAI `/chat/completions` or Anthropic `/v1/messages` protocol can be configured. NemoClaw validates custom endpoints by sending a real inference request during onboarding (rather than checking a `/models` endpoint) because many proxy servers lack standardized model listing. The trade-off is that you are responsible for ensuring the custom endpoint is reliable and correctly implements the protocol.

### Q: How mature is NemoClaw for production use?

As of March 2026, NemoClaw is explicitly alpha software. The project was released on March 16, 2026, and has not yet had a production-ready release. APIs, configuration schemas, and runtime behavior may change without notice. The project's GitHub repository shows high community interest (17,800+ stars in two weeks), but stars measure interest, not stability. For production environments, treat NemoClaw as an evaluation tool and plan for re-onboarding during upgrades.
