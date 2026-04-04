## Architecture
<!-- level: intermediate -->
<!-- references:
- [SGLang GitHub Repository](https://github.com/sgl-project/sglang) | github
- [Mini-SGLang: Efficient Inference Engine in a Nutshell](https://www.lmsys.org/blog/2025-12-17-minisgl/) | blog
- [Inside SGLang: Anatomy of a High-Performance Structured LLM Inference System](https://blog.sugiv.fyi/inside-sglang-anatomy-high-performance-structured-llm-inference-system) | blog
- [SGLang Paper](https://arxiv.org/abs/2312.07104) | paper
-->

### High-Level Design

SGLang follows a **frontend-backend co-design** architecture. The frontend provides a Python-embedded DSL for expressing structured LLM programs, while the backend runtime (called SRT -- SGLang Runtime) handles serving with aggressive optimization. These two layers are designed together so the runtime can exploit program structure captured by the frontend.

The backend itself follows a **multi-process, pipelined architecture** with three major process groups:

1. **API Server + TokenizerManager** -- handles HTTP/gRPC, tokenization, and detokenization (CPU-bound)
2. **Scheduler** -- manages request queuing, batching, memory allocation, and KV cache (CPU-bound, one per GPU group)
3. **TpModelWorker** -- runs the actual model forward passes on GPU (GPU-bound, one per tensor-parallel rank)

Communication between processes uses ZMQ (ZeroMQ) for inter-process messaging and shared memory for large tensor transfers.

### Key Components

**HTTP Server (`entrypoints/http_server.py`)** -- The entry point for all API requests. Exposes OpenAI-compatible endpoints (`/v1/chat/completions`, `/v1/completions`, `/v1/embeddings`) plus SGLang-native endpoints. It exists because the system needs to speak the same protocol as existing LLM infrastructure while supporting SGLang-specific features like structured generation and multi-modal inputs.

**TokenizerManager (`managers/tokenizer_manager.py`)** -- Converts text to token IDs and vice versa. Runs in the API server process. It exists as a separate component because tokenization is CPU-intensive and must not block the GPU scheduler. It also handles multi-modal input preprocessing (images, audio) and request normalization before forwarding to the scheduler via ZMQ.

**Scheduler (`managers/scheduler.py`)** -- The brain of the system. Manages the waiting queue, running batch, memory allocation, and all scheduling decisions. It exists because efficient GPU utilization requires sophisticated batching: the scheduler must decide which requests to prefill, which to keep decoding, when to preempt, and how to maximize KV cache hit rates. It runs a tight event loop (`event_loop_normal`) that receives requests, assembles batches, dispatches them to the model worker, and processes results -- all without Python GIL contention on the hot path.

**RadixCache (`mem_cache/radix_cache.py`)** -- The radix tree that stores and manages KV cache for prefix reuse. It exists because the naive approach (discard KV cache after each request) wastes enormous computation on shared prefixes. The radix tree enables O(n) prefix matching (where n is key length) and LRU-based eviction when GPU memory is full. This is the component that implements the RadixAttention concept.

**SchedulePolicy (`managers/schedule_policy.py`)** -- Determines request priority and ordering. It exists because cache-aware scheduling (prioritizing requests that share prefixes with cached content) dramatically improves throughput. Supports LPM (Longest Prefix Match), DFS-Weight, FCFS, and routing-key policies, with dynamic fallback from LPM to FCFS when queue depth exceeds 128 to avoid O(n*m) prefix matching overhead.

**ModelRunner (`model_executor/model_runner.py`)** -- Manages model loading, forward pass execution, and CUDA graph capture. It exists because model execution involves complex state management: weight loading, KV cache allocation, attention backend selection, LoRA adapter switching, and CUDA graph replay for decode efficiency.

**Attention Backends (`layers/attention/`)** -- Pluggable attention implementations (FlashInfer, FlashAttention, Triton). They exist because attention computation is the bottleneck for LLM inference, and different hardware (NVIDIA, AMD, Intel) and workloads (short vs long context, GQA vs MHA) benefit from different kernel implementations. FlashInfer is the default on NVIDIA GPUs.

**Grammar Backends (`constrained/`)** -- Pluggable constrained decoding engines (XGrammar, Outlines, llguidance). They exist because structured output generation requires applying grammar constraints at every decoding step, and different grammar backends offer different trade-offs between speed, expressiveness, and supported grammar types.

### Data Flow

A complete request flows through the system as follows:

1. **HTTP Request arrives** at the FastAPI server with a prompt and sampling parameters
2. **TokenizerManager** tokenizes the prompt, preprocesses multi-modal inputs, creates a `TokenizedGenerateReqInput`, and sends it to the Scheduler via ZMQ
3. **Scheduler receives** the request and adds it to the waiting queue
4. **Scheduling loop** runs: the scheduler calls `get_next_batch_to_run()`
   - Checks the RadixCache for prefix matches via `match_prefix()`
   - Applies the scheduling policy to prioritize requests (LPM sorts by longest cached prefix)
   - Builds a prefill batch using `PrefillAdder` which respects token budgets and memory constraints
   - If no new prefill fits, runs decode on the existing running batch
5. **Model forward pass** executes on GPU via `ModelRunner.forward()` with the appropriate attention backend
6. **Sampling** selects next tokens using temperature, top-p, top-k, with optional grammar mask from constrained decoding
7. **Results flow back** to the Scheduler, which updates request state, inserts new KV cache entries into the RadixCache, and streams tokens to the TokenizerManager
8. **TokenizerManager detokenizes** and streams text back to the HTTP response

### Design Decisions

**ZMQ over shared memory for control flow.** SGLang uses ZMQ for inter-process communication of control messages (requests, completions) but shared memory for large tensor data (token IDs, logprobs). This avoids serialization overhead for bulk data while keeping control flow simple and debuggable.

**Single-process scheduler (no distributed coordinator).** Unlike systems that use Ray or separate coordination services, SGLang runs one scheduler per GPU group in a single process. This eliminates distributed coordination overhead and enables microsecond-level scheduling decisions. For data parallelism across GPU groups, a lightweight `DataParallelController` routes requests to the appropriate scheduler.

**Cache-aware scheduling as default.** Most serving systems use FCFS (first-come-first-served) scheduling. SGLang defaults to LPM (Longest Prefix Match) which reorders the waiting queue to prioritize requests that can reuse the most cached KV data. This trades strict fairness for significantly higher throughput on workloads with shared prefixes.

**CUDA graph capture for decode.** SGLang captures CUDA graphs for common decode batch sizes, eliminating kernel launch overhead. This is critical because decode steps are memory-bandwidth-bound with very short kernel execution times, making CPU-side launch overhead a significant fraction of total time.
