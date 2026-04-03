## Architecture
<!-- level: intermediate -->
<!-- references:
- [Architecture Overview](https://nvidia.github.io/TensorRT-LLM/architecture/overview.html) | official-docs
- [Core Concepts](https://nvidia.github.io/TensorRT-LLM/architecture/core-concepts.html) | official-docs
- [DeepWiki - TensorRT-LLM](https://deepwiki.com/NVIDIA/TensorRT-LLM) | community
-->

### High-Level Design

TensorRT-LLM is organized into three main layers, each handling a different concern:

```
┌─────────────────────────────────────────────────────────┐
│                   Python LLM API                         │
│  (LLM class, SamplingParams, model loading, tokenizer)  │
├─────────────────────────────────────────────────────────┤
│                PyExecutor (Worker Process)                │
│  ┌──────────┐ ┌──────────────┐ ┌─────────┐ ┌─────────┐ │
│  │Scheduler │ │KVCacheManager│ │ Model   │ │ Sampler │ │
│  │          │ │              │ │ Engine  │ │         │ │
│  └──────────┘ └──────────────┘ └─────────┘ └─────────┘ │
├─────────────────────────────────────────────────────────┤
│              C++ Runtime & TensorRT Engine                │
│  (CUDA kernels, plugins, NCCL communication, executor)  │
└─────────────────────────────────────────────────────────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
           GPU 0      GPU 1     GPU N
```

The **Python LLM API** is the user-facing layer: it loads models from HuggingFace, manages tokenization, and exposes `generate()`. Underneath, it spawns one **PyExecutor** per GPU rank — a worker process that runs a continuous inference loop. Each PyExecutor contains a **Scheduler** (request admission and batching), **KVCacheManager** (paged memory allocation), **ModelEngine** (forward pass execution), and **Sampler** (token selection). At the bottom, the **C++ Runtime** handles GPU kernel execution, TensorRT engine inference, and multi-GPU communication via NCCL.

### Key Components

**Scheduler** — Decides which requests to admit and how to batch them. Exists because GPU resources (KV cache blocks, compute) are finite, and blindly admitting all requests would cause out-of-memory failures. The scheduler is split into two sub-components: a *Capacity Scheduler* that checks whether resources exist for new requests (and can pause/evict if needed), and a *Micro-Batch Scheduler* that partitions admitted requests into context (prefill) and generation batches.

**KVCacheManager** — Manages paged KV cache blocks as a memory pool. Exists because naive contiguous KV cache allocation wastes memory proportional to `max_seq_len × batch_size` even when most sequences are short. The paged approach allocates blocks on demand and recycles them when sequences finish, similar to virtual memory in an OS. Supports block reuse for prefix caching and KV cache quantization (INT8/FP8) for further memory savings.

**ModelEngine** — Wraps the compiled TensorRT engine or PyTorch model and executes forward passes. Exists as an abstraction layer that insulates the rest of the system from whether inference runs through TensorRT's compiled engine path or PyTorch's eager execution path (the two supported backends).

**Sampler** — Processes raw logits from the model and selects the next token. Supports greedy, top-k, top-p, beam search, and speculative decoding acceptance/rejection. The C++ sampler is default since v1.1, offering lower overhead than the Python equivalent.

**GenerationExecutor** — The orchestration layer that ties everything together. Manages the request lifecycle: submit → schedule → execute → sample → respond. Comes in several flavors: `GenerationExecutorWorker` (single-process), `GenerationExecutorProxy` (multi-process IPC with MPI), and `RayExecutor` (distributed via Ray).

### Data Flow

A single inference request flows through the system in this sequence:

1. **Request submission** — User calls `llm.generate("prompt")`. The LLM API tokenizes the input and submits a `GenerationRequest` to the Executor.

2. **Capacity check** — The Capacity Scheduler checks whether enough KV cache blocks exist for the new request. If yes, the request is admitted. If memory is tight, lower-priority requests may be paused to make room.

3. **Micro-batch formation** — The Micro-Batch Scheduler partitions all active requests into two groups: *context requests* (those still in prefill) and *generation requests* (those producing tokens). This split is needed because prefill processes many tokens at once (compute-bound) while generation processes one token per step (memory-bound).

4. **KV cache allocation** — The KVCacheManager allocates new blocks for context requests and extends existing allocations for generation requests (one new token per block slot).

5. **Forward pass** — The ModelEngine runs the TensorRT engine (or PyTorch model) on the combined batch. Plugins handle attention (GPTAttentionPlugin with paged KV cache), GEMM (FP8/FP4 kernels), and multi-GPU communication (NCCL all-reduce).

6. **Token sampling** — The Sampler processes output logits. For greedy decoding, it picks the highest-probability token. For speculative decoding, it validates draft tokens against the target model's distribution.

7. **Context-to-generation transition** — Requests that finish prefill move from the context batch to the generation batch. Their KV cache blocks are retained for subsequent generation steps.

8. **Response delivery** — Completed sequences (hit EOS or max length) have their KV cache blocks freed and responses returned to the user. Streaming mode delivers tokens incrementally.

9. **Loop continues** — The executor returns to step 2 for the next iteration, potentially admitting new requests into the now-freed slots.

### Design Decisions

**PyTorch as the default backend (v1.0+)** — Starting with v1.0, TensorRT-LLM switched from a custom graph-building API to PyTorch as the primary model definition and execution framework. This dramatically simplified model onboarding (new architectures can reuse HuggingFace code patterns) at the cost of slightly less optimization control. The older TensorRT-native path still exists but is no longer the recommended workflow.

**Paged KV cache over contiguous allocation** — The team adopted the [PagedAttention](https://arxiv.org/abs/2309.06180) approach (originally from vLLM) because contiguous KV cache allocation wastes 60-80% of GPU memory in typical production workloads where request lengths vary widely. Paged allocation reduces memory waste to near zero, enabling 2-3x more concurrent requests.

**C++ core with Python orchestration** — Performance-critical paths (kernel execution, KV cache management, scheduling) are implemented in C++ for minimal overhead, while model definition and user-facing APIs use Python for developer ergonomics. This split exists because Python's GIL and interpreter overhead would bottleneck the per-token scheduling loop that runs at millisecond cadence.

**Plugin architecture for specialized kernels** — Rather than relying solely on TensorRT's auto-optimization, TensorRT-LLM registers custom plugins for attention (FlashAttention), GEMM (FP8, FP4), and communication (NCCL). This exists because LLM-specific operations (multi-head attention with paged KV cache, quantized matrix multiplication) require hand-tuned kernels that TensorRT's general-purpose pattern matching cannot discover automatically.
