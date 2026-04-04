## Trade-offs & Limitations
<!-- level: intermediate -->
<!-- references:
- [SGLang vs vLLM in 2026: Benchmarks, Architecture, and When to Use Each](https://particula.tech/blog/sglang-vs-vllm-inference-engine-comparison) | blog
- [Comparing SGLANG, vLLM, and TensorRT-LLM with GPT-OSS-120B](https://www.clarifai.com/blog/comparing-sglang-vllm-and-tensorrt-llm-with-gpt-oss-120b) | blog
- [LLM Inference Engines: vLLM vs LMDeploy vs SGLang](https://aimultiple.com/inference-engines) | blog
-->

### Strengths

**Automatic KV cache reuse via RadixAttention.** No other major serving framework offers automatic, transparent prefix caching with a radix tree data structure. This provides 2-5x throughput improvement on workloads with shared prefixes (multi-turn chat, few-shot, shared system prompts) with zero user configuration required.

**Integrated constrained decoding.** SGLang has first-class support for structured output generation through multiple grammar backends (XGrammar, Outlines, llguidance). The grammar is enforced at the token level with GPU-accelerated bitmask operations, not through post-hoc filtering or retry loops.

**Day-0 model support.** SGLang consistently provides same-day support for newly released open models (Llama, Qwen, Mistral, DeepSeek, etc.). The model architecture is expressed in a clean, modular format under `srt/models/` that makes adding new models straightforward.

**Production battle-tested.** Deployed on 400,000+ GPUs, generating trillions of tokens daily at organizations like xAI, Cursor, and LinkedIn. The system has been hardened through real-world production workloads at massive scale.

**Co-designed frontend + backend.** The SGLang DSL captures program structure that the runtime exploits for optimization. This is architecturally unique -- other serving frameworks treat each request independently.

### Limitations

**Python-heavy scheduler.** The scheduler's main event loop runs in Python, which introduces GIL contention under extreme concurrency. vLLM's C++ routing implementation achieves higher throughput at 100+ concurrent requests. SGLang mitigates this with a C++ radix tree implementation (`radix_cache_cpp.py`) and ongoing efforts to move hot paths to C++, but the Python scheduler remains a bottleneck at the extreme.

**NVIDIA-centric optimization.** While SGLang supports AMD ROCm, Intel XPU, and Google TPU (via SGLang-Jax), the primary optimization effort targets NVIDIA GPUs with FlashInfer. Performance on non-NVIDIA hardware may lag behind NVIDIA-optimized deployments by 10-30%.

**Memory overhead of radix tree.** The radix tree itself consumes CPU memory for metadata (node structures, parent/child pointers, timestamps). For workloads with no prefix reuse, this is pure overhead. The per-node metadata cost is small (hundreds of bytes) but multiplied by millions of unique token sequences, it can become non-trivial. Disable with `--disable-radix-cache` if not needed.

**Complexity of tuning.** SGLang exposes many tuning knobs (chunked prefill size, scheduling policy, memory fraction, eviction strategy, page size). While defaults are good for common workloads, achieving peak performance on unusual workloads may require experimentation. The interaction between chunked prefill size and scheduling policy, for instance, is non-obvious.

**Limited multi-model serving.** Each SGLang instance serves a single base model (with optional LoRA adapters). True multi-model serving requires running multiple instances with external routing. Frameworks like NVIDIA Triton offer more integrated multi-model management.

### Alternatives Comparison

**vLLM.** The most direct competitor. vLLM uses PagedAttention (not a radix tree) for KV cache management, which provides efficient memory utilization but without automatic prefix reuse. vLLM excels at raw single-request TTFT (its C++ routing layer avoids Python GIL contention) and has a larger contributor community. Choose vLLM when prefix reuse is not important and you need absolute minimum TTFT, or when you need specific vLLM-only features like pipeline parallelism for very large models across nodes.

**TensorRT-LLM.** NVIDIA's proprietary inference engine. Achieves the highest raw throughput on NVIDIA hardware through ahead-of-time kernel optimization and TensorRT graph compilation. However, it requires model-specific compilation, has longer setup times, and is locked to NVIDIA GPUs. Choose TensorRT-LLM when you need maximum throughput on NVIDIA hardware and can afford the compilation time and vendor lock-in.

**llama.cpp / Ollama.** Optimized for running models on consumer hardware (CPUs, Apple Silicon, single GPUs). Not designed for high-throughput serving but excellent for local development, prototyping, and edge deployment. Choose when you need to run models locally without a GPU cluster.

### The Honest Take

SGLang is the best choice when your workload involves multi-turn conversations, shared system prompts, structured output, or agentic workflows where prefix sharing is common -- which covers the majority of production LLM applications. Its RadixAttention provides a genuine, measurable throughput advantage that no competitor matches. However, if your workload is purely single-shot unique prompts with extreme latency requirements, vLLM's C++ routing or TensorRT-LLM's compiled kernels may serve you better. The framework moves fast and breaks things occasionally; pinning to stable releases and testing upgrades in staging is essential.
