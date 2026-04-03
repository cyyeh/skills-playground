## How It Works
<!-- level: intermediate -->
<!-- references:
- [GPT Attention](https://nvidia.github.io/TensorRT-LLM/advanced/gpt-attention.html) | official-docs
- [Speculative Decoding](https://nvidia.github.io/TensorRT-LLM/advanced/speculative-decoding.html) | official-docs
- [Disaggregated Serving Blog](https://nvidia.github.io/TensorRT-LLM/blogs/tech_blog/blog5_Disaggregated_Serving_in_TensorRT-LLM.html) | blog
- [Numerical Precision](https://nvidia.github.io/TensorRT-LLM/reference/precision.html) | official-docs
-->

### Compilation Pipeline

The compilation pipeline transforms a HuggingFace model into an optimized GPU executable through several stages:

1. **Model loading** — Weights are loaded from a HuggingFace checkpoint or local directory. The `LLaMAConfig.from_hugging_face()` pattern maps HuggingFace config fields to TensorRT-LLM's internal representation.

2. **Network definition** — The model's forward pass is traced into a TensorRT `INetworkDefinition` graph. Each layer (attention, MLP, normalization) becomes a set of TensorRT operations. Custom plugins are inserted where hand-tuned kernels outperform auto-optimization.

3. **Optimization pass** — `optimize_model_with_config()` applies pre-build transformations: quantization (replacing linear layers with FP8/INT4 variants), plugin injection, and layer fusion planning.

4. **TensorRT compilation** — The `Builder.build_engine()` method invokes TensorRT's compiler, which:
   - Evaluates available CUDA kernel implementations for each operation on the target GPU
   - Identifies fusible operation sequences (e.g., LayerNorm + quantize → single kernel)
   - Selects optimal kernels via auto-tuning (this is why compilation takes ~28 minutes)
   - Creates optimization profiles for dynamic input shapes (variable batch size, sequence length)

5. **Serialization** — The resulting engine binary, config JSON, and managed weights are written to disk. Subsequent loads skip compilation entirely (~90 seconds to deserialize).

The engine is GPU-architecture-specific: an engine compiled on H100 cannot run on A100 or B200. This is the fundamental trade-off — maximum per-GPU optimization at the cost of portability.

### Attention Mechanisms

TensorRT-LLM implements several attention strategies that activate based on the inference phase and hardware:

**Context phase (prefill):**
- Without [Fused Multi-Head Attention](https://nvidia.github.io/TensorRT-LLM/advanced/gpt-attention.html) (FMHA): Falls back to a sequence of GPU kernels with quadratic memory overhead — viable for short sequences but prohibitive at scale.
- With FMHA enabled (default): Runs FlashAttention or FlashAttention-2 in a single kernel pass. On Hopper GPUs, FP8 context FMHA further reduces compute by using 8-bit precision for Q×K and attention×V products.

**Generation phase (decode):**
- Standard masked multi-head attention kernel that reads one new query token against the KV cache. Applies QKV bias, RoPE position embeddings, and KV cache dequantization (if INT8/FP8) on the fly.
- **Multi-Block Mode**: When `batch_size × num_heads` is less than the GPU's multiprocessor count (the GPU is underutilized), work is distributed across multiple CUDA thread-blocks per attention head to keep all SMs busy.
- **XQA (Cross-Query Attention)**: Specialized kernel for [Multi-Query Attention](https://arxiv.org/abs/1911.02150) and Grouped-Query Attention, exploiting the shared KV head structure. Enabled by default.

### Memory Management

TensorRT-LLM's memory system is built around the paged KV cache:

**Block pool** — At startup, the KVCacheManager pre-allocates a pool of fixed-size blocks (configurable: 8/16/32/64/128 tokens per block). Pool shape: `[num_blocks, num_layers, 2, num_heads, block_size, head_dim]`.

**Dynamic allocation** — When a new request arrives, the manager allocates blocks from the pool for its KV cache. As generation proceeds, new blocks are allocated one at a time. When a request completes, its blocks return to the free pool.

**Block reuse (prefix caching)** — Blocks that contain common prefixes (system prompts, shared conversation history) can be reused across requests via `storeContextBlocks()` / `findNewContextBlock()`. This avoids recomputing the KV cache for identical prefix tokens.

**KV cache quantization** — Stores cache values in INT8 or FP8 instead of FP16, cutting memory usage by 2-4x. On Blackwell GPUs, [NVFP4 KV cache](https://nvidia.github.io/TensorRT-LLM/reference/precision.html) provides 50% reduction versus FP8.

**Chunked context** — For long prompts, prefill is split into smaller token chunks processed over multiple iterations. This prevents a single long-context request from monopolizing the GPU and starving generation requests.

### Speculative Decoding

TensorRT-LLM supports [six speculative decoding methods](https://nvidia.github.io/TensorRT-LLM/advanced/speculative-decoding.html) that trade extra compute for fewer autoregressive steps:

| Method | Mechanism | Best For |
|--------|-----------|----------|
| **Draft-Target** | Small draft model generates K candidates; large target validates in one pass | When a good small model exists (e.g., LLaMA-68M for LLaMA-70B) |
| **EAGLE (1/2/3)** | Single-layer transformer predicts drafts from hidden states; EAGLE-3 supports disaggregated serving | General-purpose; no separate draft model needed |
| **Medusa** | Additional LM heads predict future tokens with tree-structured verification | When you can fine-tune extra heads |
| **Lookahead** | Two parallel branches (lookahead + verification) without extra training | No-training-required scenarios |
| **NGram** | Copies from input prompt as draft tokens | Summarization, QA where output echoes input |
| **MTP (Multi-Token Prediction)** | Generates multiple tokens per forward pass | Models trained with MTP objectives |

The core mechanism is the same: generate multiple candidate tokens cheaply, then validate them against the full model in a single forward pass. Accepted tokens skip autoregressive steps; rejected tokens trigger a rewind via `KVCacheManager.rewindKVCache()`.

### Disaggregated Serving

[Disaggregated serving](https://nvidia.github.io/TensorRT-LLM/blogs/tech_blog/blog5_Disaggregated_Serving_in_TensorRT-LLM.html) separates prefill and decode onto different GPU pools, exploiting their different hardware profiles:

- **Prefill** is compute-bound (dense matrix multiplications over many tokens) — benefits from maximum FLOPS.
- **Decode** is memory-bandwidth-bound (reading the KV cache for one token at a time) — benefits from maximum memory bandwidth.

After prefill completes on the context GPU pool, the KV cache is transferred to the generation GPU pool via MPI, UCX, or NIXL (NVIDIA's KV cache transfer protocol). On GB200 systems, this achieves 1.4x–6.1x speedups depending on the workload mix.

### Performance Characteristics

**Throughput** — On a single H100 80GB with Llama 3.3 70B FP8, TensorRT-LLM delivers ~2,780 tok/s at 100 concurrent requests, ~15% faster than vLLM (~2,400 tok/s) and SGLang (~2,460 tok/s).

**Time to first token (TTFT)** — p95 TTFT of ~1,280ms at 100 concurrent requests on H100 (vs ~1,450ms for vLLM). Chunked context and FP8 context FMHA are the main levers for reducing TTFT on long inputs.

**Inter-token latency** — Enabling all build-time optimization flags (multiple profiles, reduce fusion, paged context FMHA) yields ~54% improvement in inter-token latency.

**Cold start** — ~28 minutes for first compilation of a 70B model. Subsequent loads from cached engines take ~90 seconds. This is the primary operational cost — vLLM loads in ~62 seconds, SGLang in ~58 seconds.

**Memory** — Peak VRAM usage of 74-79GB on H100 for a 70B FP8 model, slightly higher than vLLM (71-78GB) due to TensorRT's workspace buffers.
