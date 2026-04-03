## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
<!-- references:
- [Deploying LLMs with TensorRT-LLM](https://towardsdatascience.com/deploying-llms-into-production-using-tensorrt-llm-ed36e620dac4/) | blog
- [AWS Multi-Node Deployment](https://aws.amazon.com/blogs/hpc/scaling-your-llm-inference-workloads-multi-node-deployment-with-tensorrt-llm-and-triton-on-amazon-eks/) | blog
- [Turbocharging Llama 3 with Triton](https://developer.nvidia.com/blog/turbocharging-meta-llama-3-performance-with-nvidia-tensorrt-llm-and-nvidia-triton-inference-server/) | blog
-->

### When to Use It

**High-throughput production serving on NVIDIA GPUs** — When you're running a single model (or small set of models) in production and need maximum tokens-per-second per dollar. TensorRT-LLM delivers ~15% higher throughput than vLLM at the same concurrency on H100. The ROI justifies the compilation overhead when the model serves thousands of requests daily.

**Latency-critical applications** — When p95 time-to-first-token matters: AI coding assistants, real-time chatbots, voice assistants. TensorRT-LLM achieves ~1,280ms p95 TTFT at 100 concurrent requests on H100 vs ~1,450ms for vLLM. Combined with FP8 quantization and chunked context, sub-second TTFT is achievable for most input lengths.

**Multi-GPU deployment of very large models** — When deploying 70B+ or 405B models across 4-8 GPUs with tensor or pipeline parallelism. TensorRT-LLM's NCCL-based communication plugins and disaggregated serving support are purpose-built for this scale.

**Cost optimization at scale** — When you're paying for GPU-hours and want to serve more users per GPU. NVIDIA claims up to 5.3x better total cost of ownership and nearly 6x lower energy consumption versus unoptimized inference, which compounds significantly at datacenter scale.

**Blackwell/Hopper-specific workloads** — When running on latest-generation hardware (B200, GB200, H200) and want to exploit FP8, NVFP4, and hardware-specific kernel optimizations that only TensorRT-LLM provides.

### When NOT to Use It

**Rapid prototyping or frequent model changes** — If you're swapping models weekly during development, the ~28-minute compilation per model version is prohibitive. **Use instead:** vLLM (loads in ~62s) or SGLang (~58s) for experimentation, then migrate to TensorRT-LLM for production.

**Blue-green deployments or auto-scaling from zero** — The cold start penalty means scaling up takes minutes, not seconds. If your architecture needs instances that spin up on demand, the compilation step doesn't fit. **Use instead:** Pre-compiled engine caching with warm standby instances, or use NIM containers with pre-built engines.

**Non-NVIDIA hardware** — TensorRT-LLM is NVIDIA-exclusive. If your fleet includes AMD MI300X or Intel Gaudi, it won't help. **Use instead:** vLLM (supports AMD ROCm), SGLang, or framework-native serving.

**Small teams without GPU engineering expertise** — Tuning build flags, managing engine compilation across GPU types, debugging CUDA kernel issues, and configuring Triton backends requires specialized knowledge. **Use instead:** NVIDIA NIM (wraps TensorRT-LLM with pre-optimized configs) or a managed service.

**Workloads with highly variable prompt lengths and shared prefixes** — SGLang's RadixAttention provides superior prefix caching for workloads where many requests share system prompts or conversation history. **Use instead:** SGLang for heavy prefix-sharing workloads.

### Real-World Examples

**Enterprise AI assistants** — Companies like Microsoft and Oracle Cloud Infrastructure deploy TensorRT-LLM on GB300 NVL72 systems for internal and customer-facing AI assistants, serving thousands of concurrent users with sub-second response times on models like Llama 3.1 405B.

**Multi-node scaling on AWS** — AWS published a reference architecture for [multi-node LLM deployment with TensorRT-LLM and Triton on Amazon EKS](https://aws.amazon.com/blogs/hpc/scaling-your-llm-inference-workloads-multi-node-deployment-with-tensorrt-llm-and-triton-on-amazon-eks/), demonstrating horizontal scaling of 70B models across multiple GPU instances with pipeline parallelism.

**Cost-optimized API services** — Enterprises replacing OpenAI GPT-3.5/GPT-4 API calls with self-hosted open-source models (LLaMA, Mistral) on H100 clusters, using TensorRT-LLM's FP8 quantization and in-flight batching to achieve comparable quality at a fraction of the per-token cost.

**AI coding assistants** — Development tooling companies deploying code completion models with TensorRT-LLM + Triton, leveraging speculative decoding (EAGLE) to achieve interactive-speed code suggestions on models that would otherwise be too slow for real-time use.
