## Trade-offs & Limitations
<!-- level: intermediate -->
<!-- references:
- [NemoClaw Is Not the Fix. Here Is What Is Missing.](https://augmentedmind.substack.com/p/nemoclaw-is-not-the-fix-here-is-what-is-missing) | blog
- [MAESTRO Threat Modeling - NemoClaw](https://kenhuangus.substack.com/p/maestro-threat-modeling-nemoclaw) | blog
- [OpenClaw Alternatives for Enterprise Security](https://dev.to/sebastian_chedal/openclaw-alternatives-for-enterprise-security-honest-2026-comparison-3oa2) | blog
- [NemoClaw vs OpenClaw: Key Differences Explained](https://www.yottalabs.ai/post/nemoclaw-vs-openclaw-key-differences-explained) | blog
-->

### Strengths

**Defense-in-depth security model.** NemoClaw does not rely on a single security mechanism. It layers Landlock (filesystem), seccomp (syscalls), network namespaces (egress), and inference routing (credential isolation) into a multi-barrier architecture. Compromising any one layer still leaves the others intact.

**Zero-change migration from OpenClaw.** Existing OpenClaw setups can be wrapped with NemoClaw without modifying agent skills, configurations, or messaging integrations. This significantly lowers the adoption barrier for teams already invested in the OpenClaw ecosystem.

**Operator-visible policy enforcement.** Unlike black-box security systems, NemoClaw surfaces every blocked action to the operator in real time. The TUI-based approval workflow provides transparency and control over exactly what the agent can and cannot do.

**Reproducible, auditable sandboxes.** The blueprint model guarantees that every sandbox is built from the same immutable, digest-verified specification. This makes security audits straightforward — you can verify exactly what is running by examining the blueprint version and policy files.

**Open source with a permissive license.** Apache 2.0 licensing means NemoClaw can be freely adopted, modified, and integrated into commercial products without legal friction.

### Limitations

**Linux-only for full security.** The complete security stack (Landlock, seccomp, network namespaces) only works on Linux. macOS and Windows WSL deployments run with weakened isolation — a significant limitation for organizations with mixed-platform environments.

**NVIDIA ecosystem gravity.** While NemoClaw supports multiple inference providers, it is optimized for NVIDIA's Nemotron models and DGX hardware. The Privacy Router's sensitivity classification is tightly integrated with Nemotron. Teams using exclusively non-NVIDIA models will find some features less useful.

**Early alpha maturity.** NemoClaw has been publicly available for approximately two weeks (as of March 2026). There are no production deployment case studies, no independent security audits, and APIs may change without notice. This is a significant risk for any team considering adoption.

**Operational overhead.** Running NemoClaw adds complexity: a gateway process, a sandbox container, host-side state files, policy management, and bridge processes for messaging integrations. For simple agent deployments, this overhead may not be justified.

**No Windows/macOS native support.** The requirement for Linux kernel features means NemoClaw cannot run natively on macOS or Windows. Docker Desktop and WSL provide workarounds, but the security guarantees are reduced.

### Trade-offs vs. Alternatives

**NemoClaw vs. Plain OpenClaw**

| Dimension | NemoClaw | Plain OpenClaw |
|-----------|----------|----------------|
| Security | Multi-layer kernel isolation | Relies on OS-level user permissions |
| Setup complexity | Guided wizard, ~10 min | Simple install, ~2 min |
| Platform support | Linux (full), macOS/WSL (partial) | Linux, macOS, Windows |
| Inference flexibility | Routed through gateway | Direct API calls |
| Credential safety | Host-only, never in agent | Agent has direct access |
| Operational overhead | Gateway + sandbox + policies | Minimal |
| Maturity | Alpha (weeks old) | Established (months of production use) |

**NemoClaw vs. NanoClaw**

| Dimension | NemoClaw | NanoClaw |
|-----------|----------|----------|
| Architecture | Wraps existing OpenClaw | Purpose-built containerized framework |
| Security model | Kernel-level sandbox (Landlock, seccomp) | Kubernetes-native pod isolation |
| Migration path | Zero-change from OpenClaw | Requires rewriting agent logic |
| Orchestration | Single-node, CLI-driven | Kubernetes-native, declarative |
| Scale model | Single machine | Multi-node cluster |
| Vendor alignment | NVIDIA (Nemotron, DGX) | Cloud-agnostic |

**NemoClaw vs. Custom Docker Isolation**

| Dimension | NemoClaw | Custom Docker |
|-----------|----------|---------------|
| Security depth | Landlock + seccomp + netns + inference routing | Container isolation only |
| Credential management | Built-in host-side routing | Manual secret management |
| Network policy | Dynamic TUI-based approval | Static firewall rules |
| Agent integration | Pre-built OpenClaw support | DIY integration |
| Maintenance | NVIDIA-supported blueprints | Self-maintained Dockerfiles |

### Key Risks to Evaluate

1. **Vendor lock-in trajectory.** NemoClaw is open source today, but its deep integration with NVIDIA hardware and models creates migration friction. If NVIDIA changes licensing or strategy, switching to an alternative may require significant rework.

2. **Security assumptions.** NemoClaw's security depends on the correctness of the Linux kernel's isolation primitives. Kernel vulnerabilities (especially in Landlock, which is relatively new) could undermine the entire security model. Independent security audits have not yet been published.

3. **Single-node limitation.** NemoClaw is designed for single-machine deployment. Organizations needing horizontal scaling, multi-region failover, or high-availability agent clusters will need to build their own orchestration layer on top.

4. **Rapid API changes.** As an alpha-stage project, NemoClaw's APIs, configuration formats, and runtime behavior are subject to breaking changes. Any investment in automation, tooling, or integration around NemoClaw carries the risk of frequent rework.
