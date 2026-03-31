## Common Q&A
<!-- level: all -->
<!-- references:
- [NemoClaw Documentation](https://docs.nvidia.com/nemoclaw/latest/index.html) | official-docs
- [NemoClaw GitHub Issues](https://github.com/NVIDIA/NemoClaw/issues) | github
- [NemoClaw vs Docker Isolation](https://www.katonic.ai/blog/nemoclaw-docker-isolation) | blog
- [OpenClaw vs NemoClaw](https://repello.ai/blog/openclaw-vs-nemoclaw) | blog
-->

### Q: How is NemoClaw different from just running OpenClaw in a Docker container?

Standard Docker containers isolate the container from the host at the process and filesystem level, but they don't understand agent behavior. A containerized OpenClaw can still make arbitrary network calls, send prompts to any API, and attempt to access any file within the container's filesystem. NemoClaw adds agent-aware security on top of container isolation: network egress is deny-by-default with an operator-managed allowlist, all inference calls are intercepted and routed through policy, filesystem access is restricted to specific directories via Landlock (not just container boundaries), and dangerous system calls are filtered by seccomp. Docker gives you process isolation; NemoClaw gives you behavioral control.

### Q: Can the agent override or bypass NemoClaw's security policies?

No. This is the core design principle. Security policies are enforced outside the agent's execution environment -- at the OpenShell runtime level and the Linux kernel level (Landlock, seccomp, network namespaces). The agent runs inside the sandbox and has no mechanism to modify the policies that constrain it, even if it achieves arbitrary code execution within the sandbox. This is fundamentally different from prompt-level guardrails, which rely on the model "choosing" to comply.

### Q: Does NemoClaw work with agents other than OpenClaw?

NemoClaw is specifically built for OpenClaw. However, the underlying runtime (OpenShell) supports multiple agent types including Claude Code, Cursor, and Codex. If you use a different agent, use OpenShell directly rather than NemoClaw. NemoClaw's value is the pre-configured, opinionated deployment of OpenShell tailored to OpenClaw's specific needs.

### Q: What happens when the agent tries to access a blocked network endpoint?

The connection is blocked at the network namespace boundary, logged, and surfaced in the operator's terminal UI (accessible via `openshell term`). The operator can then approve the endpoint for the current session. Session approvals persist until sandbox restart but do not modify the baseline YAML policy file, so the next sandbox restart reverts to the original allowlist. This gives operators real-time visibility and control without permanently weakening the security baseline.

### Q: Can I run NemoClaw without an NVIDIA GPU?

Yes. NemoClaw works on CPU-only machines by routing inference to cloud providers (NVIDIA Endpoints, OpenAI, Anthropic, Gemini). The GPU is only needed if you want to run local inference with Nemotron or other models via Ollama/vLLM. The sandbox isolation (filesystem, network, process) is purely CPU-based and works on any Linux machine.

### Q: How does the privacy router decide where to send inference requests?

The privacy router follows policies you configure, not heuristics or AI-based classification. You define rules that specify which requests go to local models and which go to cloud providers. The routing decision is deterministic and auditable. In the simplest configuration, all requests go to a single provider. In more complex setups, you can route based on context (e.g., requests involving files in `/sandbox/proprietary/` stay local).

### Q: Is NemoClaw production-ready?

No. NemoClaw is in alpha (early preview since March 16, 2026). APIs, configuration schemas, and runtime behavior are subject to breaking changes between releases. NVIDIA explicitly states it should not be used in production environments. Use it for development, experimentation, and to evaluate the security model, but plan for instability and breaking changes.

### Q: How much overhead does NemoClaw add?

The sandbox image is approximately 2.4 GB compressed. Memory overhead is primarily from the container runtime and OpenShell processes -- expect roughly 500 MB to 1 GB on top of OpenClaw's base usage. Inference latency overhead is minimal for cloud providers (one extra hop through the OpenShell gateway, typically sub-millisecond). Local inference latency depends on your GPU and model size. The system requires a minimum of 8 GB RAM (16 GB recommended) and 20 GB disk (40 GB recommended).

### Q: How do I update NemoClaw's security policies without restarting the agent?

Network and inference policies are hot-reloadable. Edit the YAML policy file and apply the changes using OpenShell's CLI. The new policies take effect immediately without restarting the sandbox. However, filesystem and process policies are locked at sandbox creation and require a full sandbox rebuild to change.

### Q: Can I use NemoClaw in a Kubernetes cluster?

Yes. The repository includes Kubernetes manifests in the `k8s/` directory for deploying sandboxed agents as pods. The same security policies apply at the container level within Kubernetes. This enables running NemoClaw at scale in cluster environments.

### Q: What is the relationship between NemoClaw and NeMo Guardrails?

They address different layers of AI safety. NeMo Guardrails operates at the prompt/response level -- it controls what an LLM says by steering conversations, filtering outputs, and enforcing dialog policies. NemoClaw operates at the infrastructure level -- it controls what an AI agent can do by restricting filesystem access, network egress, system calls, and inference routing. Think of NeMo Guardrails as a content filter and NemoClaw as a security sandbox. They can be used together for defense in depth.

### Q: What happens if OpenShell or NemoClaw crashes? Does the agent escape the sandbox?

No. The sandbox is a container with kernel-level restrictions (Landlock, seccomp). If OpenShell crashes, the container continues running with its restrictions intact -- the agent simply loses the ability to make inference calls and approved network connections. If the container runtime crashes, the container stops. In no scenario does a crash remove the kernel-level security boundaries.
