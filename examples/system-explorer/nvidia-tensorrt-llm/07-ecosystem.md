## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [Triton TensorRT-LLM Backend](https://github.com/triton-inference-server/tensorrtllm_backend) | github
- [Triton TensorRT-LLM User Guide](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/getting_started/trtllm_user_guide.html) | official-docs
- [NVIDIA NIM](https://developer.nvidia.com/nim) | official-docs
- [NeMo TensorRT-LLM Deployment](https://docs.nvidia.com/nemo-framework/user-guide/24.12/deployment/llm/optimized/tensorrt_llm.html) | official-docs
-->

### Official Tools & Extensions

**trtllm-serve** — OpenAI-compatible HTTP server built into TensorRT-LLM. Supports chat completions, completions, and models endpoints. The simplest path to serving: `trtllm-serve "model-name"`. Stable since v1.0.

**trtllm-bench** — Benchmarking tool for measuring throughput, latency, and TTFT under configurable load patterns. Essential for capacity planning before production deployment.

**trtllm-eval** — Evaluation tool for measuring model quality (perplexity, accuracy) after quantization. Validates that FP8/INT4 quantization hasn't degraded output quality below acceptable thresholds.

**NVIDIA ModelOpt** — Quantization calibration toolkit. Handles the data collection and scaling factor computation needed for post-training quantization (PTQ). Required for INT8 SmoothQuant and recommended for FP8. Shipped as a separate package (`nvidia-modelopt`), tightly integrated with TensorRT-LLM's quantization pipeline.

**NVIDIA NIXL** — KV cache transfer protocol for disaggregated serving. Enables efficient GPU-to-GPU KV cache migration between prefill and decode pools. Used internally by TensorRT-LLM's disaggregated serving mode alongside MPI and UCX.

### Community Ecosystem

**[Triton Inference Server](https://github.com/triton-inference-server/tensorrtllm_backend)** — The primary production serving platform for TensorRT-LLM engines. The `tensorrtllm_backend` provides a Triton model backend that wraps TensorRT-LLM with enterprise features:
- In-flight batching and paged KV cache (delegated to TRT-LLM)
- Multi-GPU via leader mode (one Triton instance per GPU group)
- Model repository management (preprocessor → engine → postprocessor pipeline)
- Multi-Instance GPU (MIG) support for sharing a single GPU across models
- LoRA adapter hot-loading
- GenAI-Perf benchmarking tool for load testing

**[NVIDIA NIM](https://developer.nvidia.com/nim)** — Containerized microservices that bundle model weights + optimized inference engine + OpenAI-compatible API into a single container. NIM automatically selects the best backend (TensorRT-LLM, vLLM, or SGLang) and builds optimized engines for the target GPU. Eliminates manual compilation and configuration — the "managed service" wrapper around TensorRT-LLM.

**[NVIDIA Dynamo](https://github.com/ai-dynamo/dynamo)** — Datacenter-scale inference orchestrator for disaggregated serving. Provides smart request routing based on KV cache locality, decoupled pre/post-processing workers, and Kubernetes-native autoscaling. Uses TensorRT-LLM as the execution engine underneath.

**[NVIDIA NeMo Framework](https://docs.nvidia.com/nemo-framework/user-guide/latest/)** — Training framework with direct export to TensorRT-LLM. Models trained with NeMo can be converted to TensorRT-LLM engines without intermediate HuggingFace conversion, streamlining the train-to-serve pipeline.

**[BentoML](https://www.bentoml.com/)** — ML serving framework with TensorRT-LLM integration. Provides a higher-level abstraction for packaging TensorRT-LLM models as containerized services with built-in scaling and monitoring.

**[LangChain / LlamaIndex](https://www.langchain.com/)** — LLM application frameworks that can connect to TensorRT-LLM via its OpenAI-compatible API endpoint (`trtllm-serve`), enabling use in RAG pipelines, agents, and multi-step reasoning chains.

### Common Integration Patterns

**TensorRT-LLM + Triton (standard production stack):**
```
Client → Triton Inference Server → tensorrtllm_backend
              │                         │
              ├── Preprocessor ──→ Tokenization
              ├── TRT-LLM Engine ──→ Inference
              └── Postprocessor ──→ Detokenization
```
This is the most common production deployment pattern. Triton handles HTTP/gRPC endpoints, request queuing, health checks, and metrics. TensorRT-LLM handles the actual inference with in-flight batching and paged attention.

**TensorRT-LLM + Dynamo (disaggregated serving):**
```
Client → Dynamo Router → Prefill Pool (GPU Group A)
                    │            │
                    │       KV Cache Transfer (NIXL)
                    │            ↓
                    └──→ Decode Pool (GPU Group B) → Response
```
For high-throughput workloads mixing long-context prefill with real-time generation. Dynamo routes requests to specialized GPU pools and manages KV cache transfer between them.

**NeMo → TensorRT-LLM → NIM (full lifecycle):**
```
Training (NeMo) → Export → Engine Build (TRT-LLM) → Container (NIM) → Deploy
```
End-to-end pipeline from model training to optimized production serving, staying within NVIDIA's ecosystem throughout.

**TensorRT-LLM + Speculative Decoding + LoRA:**
```
Base Model (FP8 Engine) ─┬─→ Main Inference
                          │
Draft Model (EAGLE head) ─┘─→ Speculative Tokens
                          │
LoRA Adapter (hot-loaded) ─→ Task-Specific Adaptation
```
Combines multiple optimization strategies: FP8 quantization for memory efficiency, EAGLE speculative decoding for latency reduction, and LoRA for task specialization without recompiling the base engine.
