## Common Q&A
<!-- level: all -->
<!-- references:
- [vLLM Optimization and Tuning](https://docs.vllm.ai/en/stable/configuration/optimization/) | official-docs
- [vLLM FAQ and Troubleshooting](https://docs.vllm.ai/en/latest/) | official-docs
-->

### Q: My GPU utilization is high but throughput is lower than expected -- what's the diagnostic playbook?

High GPU utilization doesn't guarantee high throughput. The most common culprits are: (1) **KV cache contention** -- check `gpu_cache_usage_perc` in Prometheus metrics. If it's consistently at 100%, requests are queueing for memory and you need to reduce `max-model-len` or add GPUs. (2) **Excessive preemption** -- when the KV cache fills, the scheduler preempts running requests (discarding their partial KV cache), causing wasted computation. Monitor `num_preemptions` in the metrics. (3) **Prefill bottleneck** -- long prompts tie up the GPU for prefill computation, starving decode requests. Consider enabling chunked prefill with `--enable-chunked-prefill` to interleave prefill and decode. (4) **Tensor parallelism communication overhead** -- if using TP across GPUs without NVLink, the all-reduce communication may be the bottleneck. Check NCCL profiling.

### Q: How do I right-size the `max-model-len` parameter?

`max-model-len` directly determines the maximum KV cache size per request, which determines how many concurrent requests can run. The formula is roughly: `num_concurrent_requests = available_kv_cache_memory / (max_model_len * per_token_kv_size * num_layers)`. If your actual workload rarely exceeds 4K tokens, setting `max-model-len` to 4096 instead of the model's maximum (e.g., 128K) frees enormous amounts of memory for additional concurrent requests. Always profile your actual prompt + completion lengths and set this parameter accordingly.

### Q: When should I use speculative decoding vs. just scaling with more GPUs?

Speculative decoding reduces **latency** (time per output token) at the cost of some **throughput** (the draft model consumes GPU compute). More GPUs with tensor parallelism also reduce latency but increase throughput too. Use speculative decoding when: latency is your primary concern, you have a well-matched draft model with high acceptance rates (>70%), and your GPU is already underutilized during decode (memory-bandwidth bound). Don't use it when: throughput is the priority, the draft model's acceptance rate is low (wasting verification compute), or you're already compute-bound during decode.

### Q: How does vLLM handle request preemption, and what happens to the partial KV cache?

When the KV cache is full and a higher-priority request arrives, the scheduler preempts the lowest-priority running request. The preempted request's KV cache blocks are freed (returned to the block pool), and the request moves back to the waiting queue. When the request is rescheduled, its KV cache must be recomputed from scratch -- there is no swap-to-CPU mechanism in the V1 engine. This means preemption is expensive and should be minimized by right-sizing `max-model-len` and GPU memory. Monitor `num_preemptions` -- if it's non-zero in steady state, you need more KV cache capacity.

### Q: What's the practical limit on concurrent requests, and how do I find it for my setup?

The limit depends on three factors: GPU memory (for KV cache), model size, and average sequence length. For a Llama-3.1-8B model on an A100-80GB with `max-model-len=4096`, you can typically serve 200-400 concurrent requests. For a 70B model on 4xA100-80GB with TP=4, expect 50-150 concurrent requests. To find your specific limit, gradually increase load while monitoring `gpu_cache_usage_perc` and `num_requests_waiting`. When cache usage hits 100% and waiting requests grow, you've found your ceiling.

### Q: How does prefix caching interact with LoRA adapters?

Prefix caching hashes token blocks without considering which LoRA adapter is active. This means two requests with the same token prefix but different LoRA adapters would incorrectly share KV cache blocks, producing wrong results. As of v0.19.0, vLLM supports "cache salting" -- a mechanism that incorporates the LoRA adapter identifier into the block hash, ensuring that prefix cache entries are isolated per adapter. Enable this via the appropriate configuration when using both prefix caching and LoRA adapters together.

### Q: Should I use FP8, AWQ, or GPTQ quantization?

**FP8** is the simplest: it quantizes at serve-time (no pre-quantization step), works on Hopper GPUs (H100, H200), and provides ~2x memory reduction with minimal quality loss. Use FP8 if you have Hopper hardware. **AWQ** requires a pre-quantized model but works on all CUDA GPUs and provides 4-bit quantization (~4x memory reduction) with good quality. **GPTQ** is similar to AWQ in concept but uses a different quantization algorithm. AWQ generally produces better results than GPTQ for the same bit width. Choose based on: hardware (FP8 for Hopper), available pre-quantized models (check Hugging Face for AWQ/GPTQ variants), and quality requirements.

### Q: How do I serve multiple models on the same GPU infrastructure?

Three approaches: (1) **Separate vLLM instances** per model, each bound to specific GPUs. Simplest but wastes memory if models are underutilized. (2) **LoRA adapters** on a shared base model -- use `--enable-lora` and specify adapters per request. Most memory-efficient when models share a base architecture. (3) **Ray Serve routing** in front of multiple vLLM instances, with automatic routing and autoscaling per model. Best for production multi-model deployments.

### Q: What happens when vLLM receives more requests than it can handle?

New requests enter the `waiting` queue. The scheduler will promote them to `running` as KV cache blocks become available (when existing requests finish). If the waiting queue grows without bound, clients will experience increasing latency. The API server returns streaming responses for running requests and queues non-running ones. There is no hard rejection -- requests wait indefinitely unless the client times out. In production, place a load balancer or rate limiter in front of vLLM to control admission.
