## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [SGLang Official Documentation](https://sgl-project.github.io/) | official-docs
- [SGLang GitHub Repository](https://github.com/sgl-project/sglang) | github
- [SGLang Joins PyTorch Ecosystem](https://pytorch.org/blog/sglang-joins-pytorch/) | blog
-->

### Official Tools & Extensions

**SGLang Router** -- A lightweight data-parallel request router that distributes incoming requests across multiple SGLang worker instances. Supports cache-aware routing (directing requests to workers most likely to have relevant KV cache) and round-robin fallback. Essential for multi-GPU scaling beyond tensor parallelism.

**SGLang Diffusion** -- An extension (released January 2026) that accelerates video and image generation using diffusion models. Applies SGLang's batching and scheduling optimizations to the diffusion generation pipeline, supporting models like Stable Diffusion, FLUX, and video generation models.

**sgl-kernel** -- A standalone package of optimized CUDA/Triton kernels used by SGLang: custom attention kernels, fused MoE kernels, quantization kernels (FP8/INT4), and sampling kernels. Can be installed independently for use in other projects.

**SGLang-Jax** -- A JAX backend (released October 2025) enabling SGLang to run natively on Google TPUs. Extends SGLang's reach beyond NVIDIA GPUs to the TPU ecosystem, particularly for Google Cloud deployments.

**Benchmark Suite** -- Built-in benchmarking tools (`bench_serving.py`, `bench_offline_throughput.py`, `bench_one_batch.py`) for measuring throughput, latency, and TTFT under various workloads. Compatible with standard benchmarking formats for comparison with vLLM and TGI.

### Community Ecosystem

**XGrammar** -- The default grammar backend for constrained decoding, developed by the MLC-AI team. Provides high-performance grammar-guided generation with support for JSON schemas, regex patterns, and EBNF grammars.

**FlashInfer** -- The primary attention kernel library, providing highly optimized attention implementations for both prefill (FlashAttention-style) and decode (paged attention) on NVIDIA GPUs. SGLang was one of the first adopters of FlashInfer's paged KV cache API.

**Outlines** -- An alternative grammar backend for constrained decoding, offering a different grammar compilation approach. Useful for grammars that XGrammar doesn't support or when Outlines-specific features (like regex-based generation) are needed.

**llguidance** -- Microsoft's grammar backend, offering yet another approach to constrained decoding. Supports complex grammar compositions and is integrated as a pluggable backend.

**DeepWiki SGLang Learning Materials** -- Community-maintained educational resources and documentation on SGLang internals, providing deep-dive explanations of subsystems.

### Common Integration Patterns

**SGLang + LangChain/LlamaIndex.** SGLang's OpenAI-compatible API enables drop-in integration with LangChain, LlamaIndex, and other LLM orchestration frameworks. Point the framework's `base_url` at your SGLang server and benefit from RadixAttention without code changes.

**SGLang + Kubernetes.** Deploy SGLang as a Kubernetes Deployment with GPU resource requests. Use the built-in health check endpoint (`/health`) for liveness/readiness probes. The official Docker images include all dependencies pre-installed.

**SGLang + NVIDIA Triton.** SGLang can be deployed behind NVIDIA Triton Inference Server for enterprise-grade model management, A/B testing, and multi-model serving. Triton handles routing and SGLang handles the actual LLM inference.

**SGLang + Ray Serve.** For complex serving topologies with multiple models and preprocessing steps, SGLang integrates with Ray Serve. SGLang handles the GPU-intensive model inference while Ray manages the broader serving DAG.

**SGLang + Prometheus/Grafana.** Enable `--enable-metrics` to expose Prometheus-compatible metrics. Build Grafana dashboards to monitor throughput, latency, cache hit rates, batch sizes, and memory usage in real-time.

**SGLang + LoRA Adapters.** SGLang supports serving multiple LoRA adapters on a single base model with dynamic switching. This enables multi-tenant deployments where different customers or use cases have fine-tuned adapters.
