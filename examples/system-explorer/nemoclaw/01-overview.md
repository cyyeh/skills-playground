## Overview
<!-- level: beginner -->
<!-- references:
- [NemoClaw Overview](https://docs.nvidia.com/nemoclaw/latest/about/overview.html) | official-docs
- [NemoClaw Product Page](https://www.nvidia.com/en-us/ai/nemoclaw/) | official-docs
- [NVIDIA Announces NemoClaw](https://nvidianews.nvidia.com/news/nvidia-announces-nemoclaw) | blog
- [NemoClaw GitHub Repository](https://github.com/NVIDIA/NemoClaw) | github
-->

Running an autonomous AI assistant on your own infrastructure sounds powerful until you consider what happens when that assistant has uncontrolled access to the internet, your filesystem, and your API keys. [NemoClaw](https://www.nvidia.com/en-us/ai/nemoclaw/) is NVIDIA's answer to this problem: an open-source reference stack that wraps the popular [OpenClaw](https://github.com/cline/cline) coding assistant inside a hardened sandbox with policy-controlled network access and managed inference routing.

Released as an alpha preview on March 16, 2026, NemoClaw builds on two foundational pieces from NVIDIA's [Agent Toolkit](https://docs.nvidia.com/nemoclaw/latest/about/overview.html): the OpenShell runtime for kernel-level sandboxing and the Nemotron family of open-source language models for private, local inference. Together, these give operators fine-grained control over what an always-on AI agent can see, do, and reach on the network -- without forking or patching OpenClaw itself.

Within two weeks of its launch, the project had already accumulated over 17,000 GitHub stars, signaling strong community interest in the intersection of autonomous AI agents and operational security.

### What It Is

NemoClaw is a security and orchestration layer for running OpenClaw AI coding assistants inside sandboxed containers -- like putting a skilled but untrusted contractor into a secured office where every door requires a badge swipe, every phone call is routed through a switchboard, and someone reviews every outgoing package before it leaves the building.

### Who It's For

NemoClaw targets platform engineers, DevOps teams, and security-conscious organizations that want to run always-on AI coding assistants in production or staging environments but need guarantees about network egress, filesystem isolation, and credential handling. It is especially relevant for teams already using OpenClaw who want to harden their deployment without abandoning the tool.

### The One-Sentence Pitch

NemoClaw lets you run OpenClaw as an always-on AI assistant with enterprise-grade sandboxing, network policy controls, and managed inference routing -- so your agent can code, but only within the boundaries you define.
