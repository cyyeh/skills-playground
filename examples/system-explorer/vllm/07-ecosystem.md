## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [vLLM Documentation](https://docs.vllm.ai/en/latest/) | official-docs
- [vLLM Production Stack](https://github.com/vllm-project/production-stack) | github
- [LLM Inference Frameworks Comparison 2026](https://blog.premai.io/llm-inference-servers-compared-vllm-vs-tgi-vs-sglang-vs-triton-2026/) | blog
-->

### Official Tools & Extensions

**vLLM Production Stack** -- A Kubernetes-native deployment system with Helm charts for cluster-wide vLLM deployment. Provides autoscaling, health checks, prefix-aware request routing across replicas, and monitoring integration. This is the official recommended way to run vLLM in production Kubernetes environments.

**vLLM Ascend** -- Hardware platform extension for Huawei Ascend NPUs, allowing vLLM to run on non-NVIDIA accelerators. Maintained as an official sub-project, reflecting vLLM's goal of broad hardware support.

**vLLM Omni** -- Extension for multimodal model serving, supporting vision-language models and other multi-modal architectures beyond text-only LLMs.

**Structured Output Manager** -- Built-in support for grammar-constrained decoding via JSON schemas, regular expressions, and context-free grammars. Integrated directly into the engine core so structured generation doesn't require external libraries.

### Community Ecosystem

**LangChain & LlamaIndex** -- Both major LLM frameworks support vLLM as a backend. LangChain provides `ChatVLLM` and `VLLM` classes for direct integration, while LlamaIndex supports vLLM via its LLM interface.

**Ray Serve** -- vLLM integrates with Ray Serve for distributed serving with autoscaling and prefix-aware routing. Ray's `LLMRouter` can distribute requests across multiple vLLM replicas based on prefix overlap, maximizing cache hit rates.

**OpenLLM by BentoML** -- Uses vLLM as one of its inference backends, adding model versioning, packaging, and deployment management on top of vLLM's serving capabilities.

**SkyPilot** -- Cloud-agnostic deployment tool from the same UC Berkeley lab that created vLLM. Simplifies launching vLLM on any cloud provider (AWS, GCP, Azure) with automatic spot instance management and failover.

**Aphrodite Engine** -- A community fork of vLLM optimized for specific use cases, adding features like dynamic LoRA switching and additional sampling methods. Demonstrates the extensibility of the vLLM codebase.

### Common Integration Patterns

**vLLM + Kubernetes + Prometheus** -- The most common production pattern. Deploy vLLM replicas via the Production Stack Helm chart, expose Prometheus metrics at `/metrics`, and configure horizontal pod autoscaling based on GPU cache utilization or request queue depth.

**vLLM + Ray Serve for multi-model serving** -- Use Ray Serve as a request router in front of multiple vLLM instances, each serving a different model. Ray handles routing, autoscaling, and model switching while vLLM handles the actual inference.

**vLLM + LoRA adapters for multi-tenant serving** -- Serve a single base model with multiple LoRA adapters on a single vLLM instance using `--enable-lora`. Each request specifies which adapter to use, and vLLM dynamically loads and applies the correct adapter. This is far more memory-efficient than running separate instances per adapter.

**vLLM + OpenAI client library as drop-in replacement** -- The simplest integration pattern: point any OpenAI SDK client at the vLLM server URL. No code changes needed beyond swapping the `base_url`. Works with Python, TypeScript, Go, and any other language with an OpenAI client library.

**vLLM + quantization (AWQ/GPTQ/FP8) for cost optimization** -- Pre-quantize models with AWQ or GPTQ, then serve them with vLLM's `--quantization` flag. This reduces GPU memory requirements by 50-75%, allowing larger models or more concurrent requests on the same hardware.
