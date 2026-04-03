## Trade-offs & Limitations
<!-- level: intermediate -->
<!-- references:
- [vLLM vs TensorRT-LLM vs SGLang Benchmarks](https://www.spheron.network/blog/vllm-vs-tensorrt-llm-vs-sglang-benchmarks/) | blog
- [vLLM vs TensorRT-LLM 2026 Comparison](https://medium.com/synthetic-futures/vllm-vs-tensorrt-llm-the-definitive-2026-comparison-for-llm-inference-ed0943fb81d2) | blog
- [Best LLM Inference Engines 2026](https://www.yottalabs.ai/post/best-llm-inference-engines-in-2026-vllm-tensorrt-llm-tgi-and-sglang-compared) | blog
-->

### Strengths

**Highest throughput on NVIDIA GPUs** — At every concurrency level tested on H100 (1 to 100+ concurrent requests), TensorRT-LLM delivers the highest token throughput: ~2,780 tok/s at 100 concurrent requests for Llama 3.3 70B FP8, versus ~2,400 for vLLM and ~2,460 for SGLang. This comes from kernel-level optimization that general-purpose frameworks cannot match.

**Lowest latency at production scale** — p95 TTFT of ~1,280ms at 100 concurrent requests (vs 1,450ms for vLLM). Inter-token latency of ~31ms on 4×H100 for 70B models. Combined with speculative decoding (EAGLE), effective per-token latency drops further.

**Deepest hardware exploitation** — First-to-support optimizations for each NVIDIA GPU generation: FP8 on Hopper, NVFP4 on Blackwell, CUDA Graphs, XQA kernels. No other inference engine has the same depth of hardware-specific optimization.

**Comprehensive feature set** — Disaggregated serving, 6 speculative decoding methods, 10+ quantization formats, paged attention, prefix caching, LoRA hot-loading, multi-token prediction — all in one framework. Most competitors implement 2-3 of these.

**Production-ready serving** — OpenAI-compatible API via `trtllm-serve`, Triton backend for enterprise deployments, NIM containers for zero-configuration launches. Apache 2.0 licensed with NVIDIA's backing.

### Limitations

**NVIDIA GPU lock-in** — Does not work on AMD MI300X, Intel Gaudi, or any non-NVIDIA hardware. The compiled engine format is proprietary to TensorRT. If your infrastructure roadmap includes non-NVIDIA GPUs, TensorRT-LLM creates a hard dependency.

**28-minute compilation per model version** — Every change to the model (different quantization, updated weights, new architecture) requires a full recompilation. This makes rapid iteration painful and A/B testing slow. The engine is also GPU-architecture-specific — maintaining engines for A100+H100+B200 triples the build matrix.

**Higher operational complexity** — Debugging TensorRT engine compilation failures is significantly harder than debugging PyTorch errors. Build flag tuning (`--multiple_profiles`, `--reduce_fusion`, `--gemm_plugin`) requires understanding TensorRT internals. Deploying with Triton adds another layer of configuration (model repository, batching config, leader mode for multi-GPU).

**Higher idle memory footprint** — TensorRT allocates workspace buffers at engine load time. Peak VRAM for Llama 70B FP8 on H100 is 74-79GB versus 71-78GB for vLLM, leaving less headroom for concurrent workloads.

**No model hot-swapping** — Switching the base model requires stopping the server, loading a new engine (~90s), and restarting. vLLM and SGLang support loading new models into a running process.

**Windows support deprecated** — Starting from v0.18, Windows is no longer supported. Linux-only operation (Ubuntu 22.04+ recommended).

### Alternatives Comparison

| | **TensorRT-LLM** | **vLLM** | **SGLang** |
|---|---|---|---|
| **Peak throughput** | Highest (~2,780 tok/s on H100) | Moderate (~2,400 tok/s) | Moderate (~2,460 tok/s) |
| **Cold start** | ~28 min (compile) / ~90s (cached) | ~62s | ~58s |
| **Hardware support** | NVIDIA only | NVIDIA, AMD ROCm, CPU | NVIDIA, AMD ROCm |
| **Model switching** | Recompile required | Hot-swap supported | Hot-swap supported |
| **Ease of setup** | Complex (build flags, engine mgmt) | Simple (`pip install`, run) | Simple |
| **Quantization breadth** | 10+ formats (FP8, FP4, AWQ, ...) | FP8, AWQ, GPTQ | FP8, AWQ, GPTQ |
| **Speculative decoding** | 6 methods | Draft model, EAGLE | Draft model |
| **Disaggregated serving** | Built-in (NIXL, Dynamo) | Experimental | Not built-in |
| **Prefix caching** | Block reuse | Automatic | RadixAttention (superior) |
| **Best for** | Long-term, high-throughput production | Quick deployment, flexibility | Shared-prefix workloads |

**vLLM** is the go-to alternative for teams that need quick deployment, hardware flexibility, or frequent model changes. It sacrifices ~15% throughput for dramatically simpler operations and broader hardware support.

**SGLang** excels at workloads with heavy prefix sharing (e.g., many requests with the same system prompt) thanks to RadixAttention, which provides more efficient prefix caching than TensorRT-LLM's block reuse. It's also simpler to deploy than TensorRT-LLM.

**Hugging Face TGI** is worth considering if you're already in the HuggingFace ecosystem and want straightforward serving with good-enough performance. It lacks the optimization depth of TensorRT-LLM but requires minimal configuration.

### The Honest Take

Use TensorRT-LLM when you've settled on a model, you're running on NVIDIA hardware, and throughput per dollar is your primary metric. The compilation overhead and operational complexity are real costs, but they pay for themselves at scale — if you're serving millions of requests daily, the ~15% throughput advantage over vLLM translates directly to fewer GPUs (and lower bills). For everything else — prototyping, model experimentation, multi-vendor hardware, small teams — start with vLLM and only graduate to TensorRT-LLM when you've proven the need. The worst outcome is building a complex TensorRT-LLM pipeline for a model you'll replace in two months.
