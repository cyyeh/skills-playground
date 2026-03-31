## Overview
<!-- level: beginner -->
<!-- references:
- [NemoClaw Official Documentation](https://docs.nvidia.com/nemoclaw/latest/index.html) | official-docs
- [NVIDIA NemoClaw GitHub Repository](https://github.com/NVIDIA/NemoClaw) | github
- [NemoClaw: NVIDIA's Open Source Stack for Running AI Agents You Can Actually Trust](https://dev.to/arshtechpro/nemoclaw-nvidias-open-source-stack-for-running-ai-agents-you-can-actually-trust-50gl) | blog
-->

NemoClaw is an open-source reference stack from NVIDIA that wraps the OpenClaw autonomous AI assistant with enterprise-grade security, privacy controls, and managed inference routing. Think of it as the safety harness for an autonomous AI agent: OpenClaw provides the intelligence and autonomy, while NemoClaw provides the guardrails that keep that autonomy within acceptable boundaries.

Announced at GTC 2026 on March 16, 2026, NemoClaw was created to address a fundamental tension in the AI agent space: how do you give an AI agent enough freedom to be genuinely useful while ensuring it cannot access data it shouldn't, make network calls you haven't approved, or escalate its own privileges? NemoClaw solves this by enforcing security policies at the infrastructure level -- outside the agent's reach -- rather than relying on prompts or in-agent guardrails that a sufficiently capable agent could circumvent.

### What It Is

NemoClaw is a security and deployment stack that installs NVIDIA's OpenShell runtime (part of the NVIDIA Agent Toolkit), creates a hardened sandbox environment, and routes every inference call through declarative policies. You run a single CLI command, and NemoClaw provisions a sandboxed OpenClaw agent with filesystem restrictions, network egress controls, process isolation, and a privacy router that determines whether inference requests go to local models or cloud endpoints based on your policies.

### Who It's For

NemoClaw is built for platform engineers, AI infrastructure teams, and security-conscious developers who want to deploy autonomous AI agents (specifically OpenClaw) in environments where data privacy, network security, and operational control matter. It's designed for teams that need agents running continuously -- on RTX PCs, DGX Spark systems, or cloud instances -- but cannot accept a "trust the agent" security model. If you're deploying an always-on AI assistant in an enterprise, research lab, or production environment and need to control what it can access and where its inference calls go, NemoClaw is the stack to use.

### The One-Sentence Pitch

NemoClaw gives you a one-command way to deploy OpenClaw AI agents inside a sandboxed environment where security policies are enforced at the infrastructure level, not the prompt level, so the agent literally cannot override them.
