## Overview
<!-- level: beginner -->
<!-- references:
- [vLLM Official Documentation](https://docs.vllm.ai/en/latest/) | official-docs
- [Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180) | paper
- [vLLM GitHub Repository](https://github.com/vllm-project/vllm) | github
-->

vLLM is a high-throughput, memory-efficient inference and serving engine for large language models. Born from research at UC Berkeley's Sky Computing Lab, it introduced [PagedAttention](https://arxiv.org/abs/2309.06180) -- an attention algorithm that borrows virtual memory concepts from operating systems to manage the GPU memory used during LLM inference. Where existing systems waste 60-80% of their KV cache memory to fragmentation, vLLM reduces that waste to under 4%, enabling 2-4x higher throughput on the same hardware.

Since its open-source release in 2023, vLLM has rapidly become the de facto standard for self-hosted LLM serving in production. It powers inference at companies like Meta, Mistral AI, Cohere, IBM, Roblox, and Stripe. Its OpenAI-compatible API server means teams can swap in vLLM as a drop-in replacement for proprietary APIs while keeping full control over their models and infrastructure.

### What It Is

vLLM is a library and server for running large language models efficiently on GPUs -- like a smart warehouse manager that packs goods into shelves using every square inch of space instead of leaving half the shelves empty. It takes a model (Llama, Mistral, Qwen, or any of 100+ supported architectures), loads it onto one or more GPUs, and serves inference requests at maximum throughput by eliminating the memory waste that plagues naive approaches.

### Who It's For

vLLM is for ML engineers, platform teams, and AI infrastructure builders who need to serve LLMs in production at scale. If you are deploying a chatbot, building an AI-powered product, or running batch inference over millions of documents, and you need to squeeze maximum performance from your GPU budget, vLLM is designed for you. It assumes familiarity with Python and GPU infrastructure, but its API is deliberately simple.

### The One-Sentence Pitch

vLLM lets you serve any open-weight LLM at 2-4x the throughput of naive approaches by applying operating-system-style memory management to the GPU's KV cache -- so you get more requests per GPU, lower latency, and an OpenAI-compatible API out of the box.
