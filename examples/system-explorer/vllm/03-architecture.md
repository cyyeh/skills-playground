## Architecture
<!-- level: intermediate -->
<!-- references:
- [Inside vLLM: Anatomy of a High-Throughput LLM Inference System](https://blog.vllm.ai/2025/09/05/anatomy-of-vllm.html) | blog
- [vLLM V1 Engine Architecture](https://docs.vllm.ai/en/latest/) | official-docs
- [vLLM GitHub: V1 Engine Core](https://github.com/vllm-project/vllm/tree/main/vllm/v1/engine) | github
-->

### High-Level Design

vLLM's V1 architecture is a layered system where a top-level API server delegates to an engine core that orchestrates scheduling, KV cache management, and GPU execution. The design separates concerns cleanly: the API layer handles HTTP/protocol concerns, the engine manages request lifecycle, the scheduler decides what to compute next, and the workers execute the actual model inference on GPUs.

The system follows a producer-consumer pattern: the API server produces requests, the scheduler consumes them and produces execution batches, and GPU workers consume batches and produce token outputs. Communication between the engine process and workers uses shared-memory message queues (ZMQ sockets or direct shared memory), minimizing serialization overhead.

### Key Components

**API Server (OpenAI-compatible)** -- Provides `/v1/completions`, `/v1/chat/completions`, and other OpenAI-compatible endpoints. Exists because vLLM aims to be a drop-in replacement for proprietary APIs, allowing teams to switch from OpenAI to self-hosted inference with zero client-side code changes. Built on FastAPI with async streaming support.

**LLMEngine** -- The top-level interface wrapping the engine core client. Exists to provide backward compatibility and a clean Python API for both online serving and offline batch inference. Handles input validation, tokenization, and output postprocessing. Manages the fan-out of `n > 1` parallel sampling requests.

**EngineCore** -- The computational heart of vLLM. Exists because the scheduling loop, model execution, and KV cache management need to run as a tight inner loop with minimal overhead. Contains the Scheduler, Model Executor, and KV Cache Manager. In production, runs as a separate process communicating via ZMQ sockets (the `EngineCoreProc` wrapper) to avoid GIL contention with the async API server.

**Scheduler** -- Decides which requests execute each step. Exists because continuous batching requires a fine-grained decision-maker that balances multiple constraints: token budget, KV cache capacity, request priority, and fairness. Maintains a `waiting` queue and a `running` list, promoting requests from waiting to running when resources permit, and preempting lower-priority running requests when the KV cache fills up. Supports FCFS and priority-based scheduling policies.

**KVCacheManager** -- Manages the allocation and deallocation of KV cache blocks across all requests. Exists because PagedAttention needs a virtual memory manager that maps logical token positions to physical GPU memory blocks. Uses a `BlockPool` with a free block queue and a hash-based prefix cache. Handles block allocation, eviction, and reference counting for shared prefix blocks.

**BlockPool** -- The low-level block allocator underneath the KVCacheManager. Exists because KV cache blocks need to be allocated, freed, and reused with minimal overhead -- similar to a memory allocator in an OS kernel. Maintains a doubly-linked free list for O(1) allocation and eviction, plus a hash table for prefix cache lookups.

**Model Executor** -- Manages worker processes and dispatches model execution. Two variants exist: `UniProcExecutor` for single-GPU and `MultiprocExecutor` for multi-GPU. Exists because multi-GPU execution requires process management, inter-process communication, and synchronization that the engine core shouldn't handle directly. The multi-proc executor spawns one process per GPU rank and uses shared-memory message queues for low-latency RPC.

**GPU Worker** -- Per-GPU process that initializes the device, loads model weights, allocates KV cache tensors, and executes forward passes. Exists because each GPU needs its own CUDA context and memory management. Contains a `ModelRunner` that handles the actual `torch` operations: building input tensors, running the model, managing CUDA graphs, and sampling output tokens.

**Model Runner** -- Executes the actual model forward pass within a GPU worker. Exists to encapsulate all the complexity of preparing inputs (packing sequences, managing attention masks, handling position IDs) and running the model with either eager mode or captured CUDA graphs. The V1 model runner (`gpu_model_runner.py` at 310KB) is the largest single file in the codebase -- reflecting the enormous complexity of efficient GPU execution.

### Data Flow

A complete request lifecycle flows through the system in these steps:

1. **Request arrival:** A client sends a POST to `/v1/chat/completions`. The API server validates the request and creates an `EngineCoreRequest` with tokenized input, sampling parameters, and a unique request ID.

2. **Engine dispatch:** The request is sent to the `EngineCore` (running in a separate process) via ZMQ socket. The engine calls `scheduler.add_request()`, which places the request in the `waiting` queue.

3. **Scheduling:** On each `step()`, the scheduler first processes running requests (allocating KV cache blocks for new tokens), then attempts to promote waiting requests. For each waiting request, it checks prefix cache hits, available KV cache blocks, and token budget. Requests that fit are moved to `running`.

4. **Execution:** The scheduler output (which requests to run, their token positions, block mappings) is passed to the Model Executor, which broadcasts it to GPU workers. Each worker builds input tensors and executes the model forward pass. For multi-GPU, tensor parallelism shards the computation across GPUs with NCCL all-reduce synchronization.

5. **Sampling:** After the forward pass, the model runner extracts the logits for the last token of each sequence and samples the next token according to each request's `SamplingParams` (temperature, top_p, top_k).

6. **Output processing:** Sampled tokens are returned to the engine core, which updates the scheduler. Finished requests (hit max tokens or stop token) are removed and their KV cache blocks freed. Unfinished requests continue to the next step. Outputs are sent back through ZMQ to the API server, which streams them to the client.

### Design Decisions

**Separate engine process:** The EngineCore runs in its own process to avoid GIL contention with the async API server. This was a deliberate choice over async-only designs -- the scheduling and KV cache management are CPU-intensive operations that would block the event loop.

**Shared-memory message queues over gRPC:** Communication between processes uses ZMQ sockets and shared memory rather than gRPC or REST. This reduces serialization overhead and latency, which matters when the engine loop runs at 100+ iterations per second.

**Flattened sequence representation:** All sequences in a batch are flattened and concatenated into a single "super sequence" for the forward pass, with position indices ensuring each sequence only attends to its own tokens. This was chosen over padded batching because it eliminates wasted computation on padding tokens.

**Block table indirection:** Rather than allocating contiguous memory per sequence, vLLM uses a block table (analogous to a page table in OS virtual memory) to map logical token positions to physical block locations. This single design decision is what enables PagedAttention's near-zero fragmentation.
