## Common Q&A
<!-- level: all -->
<!-- references:
- [NemoClaw Developer Guide - Overview](https://docs.nvidia.com/nemoclaw/latest/about/overview.html) | official-docs
- [NVIDIA NemoClaw: What It Secures, and Why It Matters](https://emelia.io/hub/nvidia-nemoclaw-explained) | blog
- [NemoClaw Is Not the Fix. Here Is What Is Missing.](https://augmentedmind.substack.com/p/nemoclaw-is-not-the-fix-here-is-what-is-missing) | blog
- [MAESTRO Threat Modeling - NemoClaw](https://kenhuangus.substack.com/p/maestro-threat-modeling-nemoclaw) | blog
-->

### Q1: Does NemoClaw replace OpenClaw?

No. NemoClaw is a complementary security layer, not a replacement. It wraps an existing OpenClaw installation inside a hardened sandbox with managed inference and network controls. Your existing OpenClaw agent — its skills, memory, configuration, and messaging integrations — runs unchanged inside the NemoClaw sandbox. Think of NemoClaw as adding walls, locks, and a security guard to a house that already exists.

### Q2: Can an agent inside the sandbox bypass the security controls?

The security controls operate at the kernel level, outside the agent's process. Landlock filesystem policies are applied by the OpenShell supervisor before the agent process starts and are locked — the agent cannot modify them. seccomp filters are similarly locked at container creation. The network namespace gives the agent a completely separate view of the network — it cannot even see the host's interfaces. However, no sandbox is perfectly escape-proof. NemoClaw provides defense-in-depth, not absolute guarantees. Kernel vulnerabilities, container runtime escapes, or novel attack techniques could theoretically bypass controls. Regular updates and security audits remain essential.

### Q3: How much latency does inference routing add?

The inference routing through the OpenShell gateway adds minimal overhead — typically single-digit milliseconds for the proxy hop. The actual latency is dominated by the inference provider's response time (which ranges from hundreds of milliseconds to seconds depending on the model and input). For most use cases, the routing overhead is negligible compared to model inference time.

### Q4: Can I use NemoClaw with non-OpenClaw agents?

NemoClaw is designed specifically for OpenClaw integration. The CLI plugin, blueprint, and onboarding flow all assume OpenClaw as the agent runtime. However, the underlying OpenShell runtime is agent-framework-agnostic. If you want sandbox isolation for a different agent framework, you can use OpenShell directly without NemoClaw. NemoClaw's value is the pre-packaged, tested integration with OpenClaw.

### Q5: What happens when the agent needs a new network endpoint?

The deny-all-by-default policy blocks the connection immediately. The blocked request appears in the operator's terminal UI (`openshell term`) with full context: destination host, port, and the binary that made the request. The operator can approve or deny it in real time. Approved endpoints persist for the current session but do not modify the baseline policy file. For permanent changes, the operator edits `openclaw-sandbox.yaml` and reapplies the policy. Preset policy files exist for common integrations like PyPI, Docker Hub, Slack, and Jira.

### Q6: Does NemoClaw work on macOS or Windows?

Partially. NemoClaw's full security stack (Landlock, seccomp, network namespaces) requires Linux. On macOS with Apple Silicon, NemoClaw runs using Colima or Docker Desktop, but the kernel-level isolation is weaker because macOS does not support Landlock or Linux-native seccomp. On Windows, NemoClaw requires WSL2 with Docker Desktop. The sandbox runs inside the WSL Linux environment, which provides most Linux security features but adds another layer of abstraction. For production deployments with full security guarantees, Linux is the recommended platform.

### Q7: How do credentials stay safe if the agent is compromised?

API credentials (for inference providers and messaging platforms) are stored on the host at `~/.nemoclaw/credentials.json` and never copied into the sandbox. The agent communicates with `inference.local`, a virtual endpoint inside its network namespace. The OpenShell gateway on the host attaches credentials to outbound requests. Even if an attacker gains code execution inside the sandbox, they cannot read the credentials file (Landlock blocks access), cannot see the host's filesystem (container isolation), and cannot intercept the gateway's credential attachment (different network namespace).

### Q8: Is NemoClaw production-ready?

No. As of March 2026, NemoClaw is in alpha (early preview). NVIDIA explicitly states that the software is not production-ready and that interfaces, APIs, and behavior may change without notice. It should be used for evaluation, development, and testing — not for production workloads handling sensitive data. The project has been publicly available for approximately two weeks and has not been battle-tested at scale.

### Q9: What is the Privacy Router?

The Privacy Router is NemoClaw's intelligent model routing layer that classifies each query by data sensitivity. Queries containing PII, proprietary code, financial data, or other sensitive categories are automatically routed to a local Nemotron model — they never leave your infrastructure. Non-sensitive queries can be routed to cloud models for faster or more capable responses. This allows teams to balance privacy requirements with model capability, using local models as a privacy floor and cloud models as a capability ceiling.

### Q10: How does NemoClaw handle agent updates and blueprint versioning?

The plugin enforces version constraints when resolving blueprints. Each blueprint artifact is immutable and identified by a cryptographic digest. When NVIDIA publishes a new blueprint version, the plugin checks compatibility with the installed OpenShell and OpenClaw versions before applying the update. If the digest does not match the expected value, the update is rejected. This prevents supply-chain attacks where a tampered blueprint could modify the sandbox's security posture. Re-running onboard with a new blueprint version recreates the sandbox from scratch — there is no in-place upgrade mechanism.
