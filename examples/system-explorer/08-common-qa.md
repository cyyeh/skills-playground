## Common Q&A
<!-- level: all -->
<!-- references:
- [Performance Tuning Guide](https://nvidia.github.io/TensorRT-LLM/performance/performance-tuning-guide/index.html) | official-docs
- [Speculative Decoding](https://nvidia.github.io/TensorRT-LLM/advanced/speculative-decoding.html) | official-docs
- [GPT Attention](https://nvidia.github.io/TensorRT-LLM/advanced/gpt-attention.html) | official-docs
-->

### Q: How do I handle the 28-minute cold start in a production environment?

The compilation only happens once per model + GPU architecture combination. The workflow is: compile the engine as a build step (CI/CD or manual), save the compiled engine to persistent storage (S3, NFS, local disk), and mount/load it at serving time. Loading a pre-compiled engine takes ~90 seconds. For rolling deployments, keep warm standby instances with engines pre-loaded. NVIDIA NIM handles this automatically — it caches compiled engines per GPU type and skips recompilation on subsequent launches. If you're managing this yourself, the key files to persist are `rank*.engine` and `config.json` from the engine directory.

### Q: When should I use FP8 versus INT4 AWQ versus NVFP4 quantization?

**FP8** is the default recommendation for Hopper GPUs (H100, H200): it provides 1.4-2.3x speedup with minimal quality loss and is the most battle-tested quantization format. **INT4 AWQ** cuts memory by 4x versus FP16 (fitting 70B models on a single 80GB GPU) but has measurable quality degradation on reasoning tasks — use it when memory is the constraint, not quality. **NVFP4** is Blackwell-only (B200, GB200) and provides 50% memory savings versus FP8 with hardware-accelerated dequantization — use it if you're on Blackwell hardware. General rule: start with FP8, measure quality, and only drop to INT4/FP4 if you need the memory savings. Use `trtllm-eval` to validate quality after quantization.

### Q: What's the practical scaling limit for tensor parallelism?

Tensor parallelism (TP) works well up to 8 GPUs within a single node connected via NVLink/NVSwitch. Beyond 8 GPUs, the all-reduce communication overhead grows faster than the compute savings, especially for smaller models. For a 70B model, TP=4 on H100 is the sweet spot (~1,564 tok/s throughput). Going to TP=8 adds ~10% throughput but doubles GPU cost. For models larger than 70B (e.g., Llama 405B), combine TP=8 within a node with pipeline parallelism (PP) across nodes. The `--pp_reduce_scatter` flag helps for MoE models like Mixtral where expert parallelism (EP) is more efficient than TP for the MoE layers.

### Q: How do I diagnose why my throughput is lower than expected?

Start with `trtllm-bench` to establish a baseline with synthetic data — this isolates model performance from tokenization and network overhead. Key metrics to check: (1) **KV cache utilization** — if `getNumFreeBlocks()` is near zero, you're memory-constrained; reduce `max_batch_size` or enable KV cache quantization (INT8/FP8). (2) **Batch size at saturation** — throughput plateaus when the GPU is fully utilized; check `IterationStats` for average batch size. (3) **Build flags** — verify `--multiple_profiles`, `--use_paged_context_fmha`, and `--reduce_fusion enable` are set. Missing these flags alone accounts for ~30% throughput loss. (4) **Chunked context** — if TTFT spikes when processing long inputs, enable `enable_chunked_context` to prevent prefill from blocking generation. (5) **GEMM plugin** — for FP8, disable `--gemm_plugin` (TensorRT's native FP8 GEMM is faster than the plugin).

### Q: Can I hot-swap models or LoRA adapters without recompiling?

**LoRA adapters**: Yes. TensorRT-LLM supports loading and swapping LoRA adapters at runtime via `LoRARequest`. The base engine is compiled once, and adapters are loaded as additional weight matrices. This works with both the Python API and Triton backend.

**Base models**: No. Swapping the base model requires compiling a new engine (~28 minutes). This is a fundamental architectural constraint — the engine binary is specialized to a specific model architecture and weight configuration. If you need fast model switching, consider: (1) keeping multiple pre-compiled engines on disk and restarting the server with the new engine (~90s), (2) using vLLM for the model exploration phase and TensorRT-LLM only for the production model, or (3) using NVIDIA NIM which pre-caches engines for popular models.

### Q: How does TensorRT-LLM handle request cancellation and timeouts?

The `Executor.cancelRequest(requestId)` API immediately marks a request for termination. The scheduler removes it from the active batch at the next iteration, and its KV cache blocks are freed. This is useful for implementing client-side timeouts — if a user disconnects, cancel the request to free resources. In the Python API, `generate_async()` returns a future that can be cancelled. For Triton deployments, the `tensorrtllm_backend` supports gRPC cancellation signals. Note: tokens generated before the cancellation call are not rolled back — cancellation takes effect at the next scheduling iteration (typically <10ms latency).

### Q: What happens when KV cache runs out of blocks during serving?

The behavior depends on the capacity scheduling policy. With **GuaranteedNoEvict** (default), new requests are queued (not admitted) until existing requests complete and free blocks — no request ever loses its cache mid-generation. With **MaxUtilization**, the scheduler may pause lower-priority in-progress requests (evicting their KV cache blocks) to make room for new requests — paused requests restart from scratch when resources free up. In practice, the key tuning lever is the KV cache memory fraction: allocating 90% of free GPU memory to KV cache (the default) usually prevents cache exhaustion unless you're running at very high concurrency with long sequences. Monitor `getNumFreeBlocks()` — if it consistently hits zero, either reduce `max_batch_size`, enable KV cache quantization, or add more GPUs.

### Q: How does disaggregated serving compare to standard serving for my workload?

Disaggregated serving benefits workloads with **bimodal request patterns**: long context inputs (1K+ tokens) mixed with short generation outputs, or vice versa. The speedup comes from separating compute-bound prefill onto GPUs optimized for throughput and memory-bound decode onto GPUs optimized for bandwidth. On GB200, benchmarks show 1.4x-6.1x speedups depending on the model and workload mix (DeepSeek R1: 1.4-2.5x; Qwen 3: 1.7-6.1x). However, disaggregated serving adds operational complexity (two GPU pools, KV cache transfer networking, routing logic) and requires NIXL/MPI/UCX for cache transfer. If your workload has uniform request sizes and moderate concurrency, standard serving is simpler and sufficient. Start with standard serving, benchmark with `trtllm-bench`, and only move to disaggregated if prefill latency is your bottleneck.
