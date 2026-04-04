## Overview
<!-- level: beginner -->
<!-- references:
- [SGLang Official Documentation](https://sgl-project.github.io/) | official-docs
- [SGLang GitHub Repository](https://github.com/sgl-project/sglang) | github
- [SGLang: Efficient Execution of Structured Language Model Programs (Paper)](https://arxiv.org/abs/2312.07104) | paper
- [SGLang Joins PyTorch Ecosystem](https://pytorch.org/blog/sglang-joins-pytorch/) | blog
-->

SGLang is a high-performance open-source framework for serving large language models (LLMs) and vision-language models (VLMs). Developed by the SGLang team (originally out of LMSYS at UC Berkeley), it combines a **frontend programming language** for expressing complex LLM programs with a **backend runtime engine** that aggressively optimizes execution. The system has seen rapid adoption since its release, now deployed on over 400,000 GPUs worldwide and trusted by organizations including xAI, AMD, NVIDIA, Intel, LinkedIn, and Cursor.

What sets SGLang apart from other serving frameworks is its co-designed approach: the frontend language captures the *structure* of LLM programs (branching, forking, constrained outputs), and the runtime exploits that structure to dramatically reduce redundant computation -- particularly through its novel [RadixAttention](https://www.lmsys.org/blog/2024-01-17-sglang/) mechanism for automatic KV cache reuse.

### What It Is

SGLang is a serving engine and programming framework for LLMs -- like a high-performance restaurant kitchen where the head chef (the scheduler) manages dozens of orders simultaneously, reuses prep work across similar dishes (KV cache sharing), and ensures every plate leaves the kitchen as fast as possible by batching similar cooking steps together.

### Who It's For

SGLang is for ML engineers and platform teams who need to serve LLMs in production at scale. It is especially valuable for teams building applications with complex multi-turn conversations, structured output generation (JSON, code), agentic workflows with branching logic, or any scenario where multiple LLM calls share common prefixes.

### The One-Sentence Pitch

SGLang is the fastest open-source LLM serving engine that automatically reuses computation across requests through RadixAttention, delivering up to 5x higher throughput than alternatives on structured LLM workloads.
