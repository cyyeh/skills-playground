## Overview
<!-- level: beginner -->
<!-- references:
- [TensorRT-LLM Overview](https://nvidia.github.io/TensorRT-LLM/overview.html) | official-docs
- [TensorRT-LLM GitHub](https://github.com/NVIDIA/TensorRT-LLM) | github
- [NVIDIA Developer Page](https://developer.nvidia.com/tensorrt-llm) | official-docs
-->

NVIDIA TensorRT-LLM is an open-source library that accelerates large language model (LLM) inference on NVIDIA GPUs. It compiles model architectures into highly optimized GPU executables, applies advanced batching and memory management techniques, and delivers the highest throughput available on NVIDIA hardware — up to 8x faster inference compared to unoptimized frameworks.

Built on PyTorch and TensorRT, TensorRT-LLM handles the full pipeline from model loading to serving: it converts HuggingFace checkpoints into optimized engines, manages GPU memory with paged KV caches, and dynamically batches requests using in-flight (continuous) batching. It supports 40+ model architectures including LLaMA, Mistral, DeepSeek, Qwen, and Gemma.

### What It Is

TensorRT-LLM is an inference compiler and runtime for LLMs — like a JIT compiler for neural networks that analyzes your model, fuses operations together, selects the fastest GPU kernels, and packages everything into a single optimized binary tuned specifically for your GPU. Where a standard PyTorch model runs operations one at a time, TensorRT-LLM pre-plans the entire execution graph for maximum GPU utilization.

### Who It's For

ML engineers and infrastructure teams deploying LLMs at scale on NVIDIA GPUs in production. Particularly valuable for organizations running long-lived, single-model deployments where throughput per dollar matters — think AI coding assistants, enterprise chatbots, or API services handling thousands of concurrent users on [H100](https://www.nvidia.com/en-us/data-center/h100/), [B200](https://www.nvidia.com/en-us/data-center/b200/), or GB200 clusters.

### The One-Sentence Pitch

TensorRT-LLM squeezes maximum inference throughput from NVIDIA GPUs by compiling LLMs into hardware-optimized engines with built-in continuous batching, paged attention, and multi-GPU parallelism.
