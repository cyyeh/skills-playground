## Overview
<!-- level: beginner -->
<!-- references:
- [NVIDIA NemoClaw Developer Guide](https://docs.nvidia.com/nemoclaw/latest/index.html) | official-docs
- [NVIDIA Announces NemoClaw for the OpenClaw Community](https://nvidianews.nvidia.com/news/nvidia-announces-nemoclaw) | press-release
- [NemoClaw GitHub Repository](https://github.com/NVIDIA/NemoClaw) | github
-->

NemoClaw is an open-source reference stack from NVIDIA that makes it safer to run OpenClaw autonomous AI agents. It wraps the popular OpenClaw always-on assistant framework inside NVIDIA's OpenShell security runtime, adding hardened sandboxing, managed inference routing, and layered network policies — all without requiring you to rip out your existing OpenClaw setup.

Announced at NVIDIA GTC on March 16, 2026, NemoClaw was born from a practical problem: OpenClaw agents can browse the web, execute code, install packages, and interact with external services — powerful capabilities that also create serious security risks when running autonomously. NemoClaw addresses this by placing the agent inside an isolated container with Landlock filesystem restrictions, seccomp syscall filtering, and network namespace isolation, while routing all inference calls through a controlled gateway that keeps API credentials off the agent's machine.

### What It Is

NemoClaw is a security and orchestration layer for autonomous AI agents. It consists of two main components: a TypeScript CLI plugin that integrates with OpenClaw's command-line interface, and a Python blueprint that orchestrates sandbox creation, security policy enforcement, and inference routing through NVIDIA's OpenShell runtime. Think of it as a "security wrapper" — it takes an existing OpenClaw agent and places it inside a locked-down environment where every network connection, filesystem access, and model API call is controlled and auditable.

### Who It's For

NemoClaw is built for enterprise teams and developers who want to run OpenClaw autonomous agents with stronger security guarantees. If you are already using OpenClaw and want to add defense-in-depth before deploying agents in production, NemoClaw provides a guided path to sandbox your agents without starting from scratch. It is also relevant to security engineers evaluating the safety posture of agentic AI systems, and to platform teams building internal infrastructure for AI agent deployment.

### The One-Sentence Pitch

NemoClaw lets you run always-on OpenClaw AI agents inside a hardened sandbox with managed inference routing, network egress controls, and operator-approved policy enforcement — all installable with a single command.
