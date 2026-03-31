## Overview
<!-- level: beginner -->
<!-- references:
- [NVIDIA NemoClaw GitHub](https://github.com/NVIDIA/NemoClaw) | github
- [NVIDIA Announces NemoClaw](https://nvidianews.nvidia.com/news/nvidia-announces-nemoclaw) | announcement
- [NemoClaw Developer Guide](https://docs.nvidia.com/nemoclaw/latest/index.html) | official-docs
- [NVIDIA NemoClaw Product Page](https://www.nvidia.com/en-us/ai/nemoclaw/) | official-docs
-->

NemoClaw is NVIDIA's open-source reference stack for running secure, always-on AI agents. Announced at GTC 2026 on March 16, 2026, it wraps the OpenClaw AI assistant framework with NVIDIA's OpenShell runtime to provide enterprise-grade security, privacy routing, and managed inference for autonomous AI agents. Think of it as a hardened container and control plane that lets organizations deploy powerful AI agents while maintaining strict governance over what those agents can access, communicate with, and execute.

NemoClaw was born from a clear enterprise need: as AI agents became more capable — browsing the web, writing code, calling APIs, managing files — the security implications of giving an LLM autonomous access to corporate infrastructure became a critical concern. NemoClaw addresses this by enforcing security policies outside the agent's process, meaning even a fully compromised agent cannot bypass its own constraints.

### What It Is

NemoClaw is a security and orchestration layer that sits between an AI agent (OpenClaw) and the outside world. It is not a model, not a framework for building agents from scratch, and not a prompt engineering toolkit. Instead, it is a runtime environment that:

- **Sandboxes** the agent in an isolated container with kernel-level filesystem, network, and process restrictions
- **Routes inference** through a managed gateway, so the agent never holds API credentials directly
- **Enforces network policies** via declarative YAML rules with deny-by-default outbound connectivity
- **Provides privacy routing** to send sensitive queries to local Nemotron models while routing non-sensitive queries to cloud providers
- **Logs every action** for audit compliance in regulated industries

### Who It's For

NemoClaw targets enterprise teams, DevOps engineers, and AI platform architects who need to deploy autonomous AI agents in production environments where security, compliance, and data sovereignty are non-negotiable. It is particularly relevant for organizations in healthcare (HIPAA), financial services (SOX, PCI-DSS), and government (data residency requirements) that want to leverage agentic AI without exposing sensitive infrastructure.

### The One-Sentence Pitch

NemoClaw gives you the security perimeter, policy enforcement, and privacy routing needed to run autonomous AI agents in production — so your agent can be powerful without being dangerous.
