## How It Works
<!-- level: intermediate -->
<!-- references:
- [PagedAttention Paper](https://arxiv.org/abs/2309.06180) | paper
- [vLLM Optimization and Tuning Guide](https://docs.vllm.ai/en/stable/configuration/optimization/) | official-docs
- [Automatic Prefix Caching Documentation](https://docs.vllm.ai/en/latest/features/automatic_prefix_caching/) | official-docs
-->

### PagedAttention Memory Management

PagedAttention is the foundational algorithm that makes vLLM's memory efficiency possible. It applies the operating system concept of virtual memory paging to the KV cache.

**The problem it solves:** During autoregressive generation, each request needs to store its KV cache -- the key and value tensors from every attention head at every layer for every token generated so far. For a 13B-parameter model, each token's KV cache entry is approximately 800 bytes. A sequence of 2048 tokens thus requires about 1.6MB of contiguous GPU memory. With hundreds of concurrent requests, allocating contiguous blocks leads to severe fragmentation -- exactly the same problem that plagued early operating systems before virtual memory.

**How it works:**
1. The KV cache is divided into fixed-size **blocks**, each storing KV data for a fixed number of tokens (16 by default).
2. A **block table** maps each request's logical token positions to physical block locations in GPU memory -- just like a page table maps virtual addresses to physical page frames.
3. When a request needs more KV cache space, the BlockPool allocates blocks from a free list. Blocks don't need to be contiguous.
4. When a request finishes, its blocks are returned to the free list immediately, making them available for new requests.
5. The custom PagedAttention CUDA kernel reads the block table to gather the correct KV data during the attention computation, handling the non-contiguous layout transparently.

This approach reduces memory waste from the last block of each request (internal fragmentation) to at most `block_size - 1` tokens per request -- under 4% waste in practice.

### Continuous Batching Scheduler

vLLM's scheduler implements iteration-level (continuous) batching, making scheduling decisions at every single generation step rather than at the batch level.

**The scheduling loop:**

Each call to `EngineCore.step()` triggers the following:

1. **Process running requests:** For each request in the `running` list, the scheduler calls `KVCacheManager.allocate_slots()` to reserve blocks for the next token. If the KV cache is full, it preempts the lowest-priority running requests (moving them back to `waiting`) to free blocks.

2. **Promote waiting requests:** The scheduler iterates through the `waiting` queue (ordered by policy -- FCFS or priority). For each candidate, it checks: (a) would adding this request exceed `max_num_running_reqs`? (b) does the remaining token budget accommodate this request's prefill? (c) can the KVCacheManager allocate the needed blocks? If all checks pass, the request moves to `running`.

3. **Build scheduler output:** The scheduler constructs a `SchedulerOutput` containing the batch of requests to execute, their block tables, sampling parameters, and any metadata needed by the model runner.

The result is that the GPU is never idle waiting for a batch to complete. As soon as one request finishes and frees KV cache blocks, a new request from the waiting queue can immediately take its place.

### Prefix Caching Mechanism

Automatic Prefix Caching (APC) identifies when multiple requests share the same prompt prefix and reuses the cached KV blocks instead of recomputing them.

**How the hash-based lookup works:**
1. When a request arrives, the scheduler hashes its prompt tokens in block-sized chunks (16 tokens per block).
2. Each hash is looked up in the BlockPool's `BlockHashToBlockMap` -- a global hash table mapping block hashes to physical KV cache blocks.
3. If a matching block is found (cache hit), the request reuses that physical block by incrementing its reference count. No KV computation is needed for those tokens.
4. If no match is found (cache miss), new blocks are allocated and populated during the prefill forward pass. These blocks are then registered in the hash table for future requests to reuse.
5. When a block's reference count drops to zero (no active request uses it), it becomes an eviction candidate but stays in the hash table. It is only evicted when the system needs free blocks.

This approach is especially powerful for multi-turn chat (where every message resends the conversation history) and document Q&A (where the same document is queried repeatedly).

### Speculative Decoding Pipeline

Speculative decoding reduces generation latency by parallelizing what would otherwise be sequential token generation.

**The propose-verify cycle:**
1. **Draft proposal:** A small, fast draft model (e.g., EAGLE, Medusa, or an n-gram predictor) generates `k` candidate tokens in sequence. Because the draft model is much smaller, this is fast.
2. **Batch verification:** The full target model runs a single forward pass over all `k` candidate tokens simultaneously. This is efficient because the forward pass can process multiple tokens in parallel (unlike autoregressive generation which is sequential).
3. **Accept/reject:** The system compares each draft token against what the target model would have produced. Correct guesses are accepted. At the first mismatch, the system keeps the target model's token and discards subsequent draft tokens.
4. **Repeat:** The process repeats from the last accepted token.

The EAGLE proposer (`vllm/v1/spec_decode/eagle.py`) uses the target model's hidden states to predict future tokens via a lightweight head, achieving high acceptance rates. The `_greedy_sample()` method converts draft hidden states to token IDs via argmax over logits, and an iterative loop generates multiple speculative tokens per step.

### Multi-GPU Execution

vLLM supports two forms of model parallelism for serving models that don't fit on a single GPU.

**Tensor Parallelism (TP):** Each GPU holds a shard of every layer's weight matrices. During a forward pass, each GPU computes its portion of the matrix multiplication, then the results are combined via NCCL all-reduce. This adds communication overhead but keeps latency low because all GPUs contribute to every token. Best for GPUs connected via fast interconnects (NVLink within a node).

**Pipeline Parallelism (PP):** Each GPU holds a contiguous subset of layers. Activations flow from GPU 0 (first layers) to GPU N (last layers) via point-to-point transfers. The `MultiprocExecutor` spawns one process per GPU rank and uses shared-memory message queues (`rpc_broadcast_mq` and `worker_response_mq`) for dispatching work. A `step_with_batch_queue()` variant in the EngineCore maintains an async queue of futures to reduce pipeline bubbles.

**Combined TP + PP:** For very large models across multiple nodes, vLLM can use TP within each node (fast NVLink) and PP across nodes (slower network). The world size must satisfy `world_size == tp_size * pp_size`.

### CUDA Graph Optimization

vLLM uses CUDA graphs to reduce CPU-side overhead during the decode phase, where each step generates only one token per request and the GPU computation is very fast.

**Two execution modes:**
1. **Eager mode:** Standard PyTorch execution where each operation is dispatched individually. Used for variable-shape operations (prefill with different sequence lengths).
2. **Captured mode:** A CUDA graph is recorded during warmup, capturing the entire forward pass as a single replayable unit. Used for fixed-shape decode operations where the input shape is predictable.

The CUDAGraph dispatcher (`vllm/v1/cudagraph_dispatcher.py`) selects between modes based on the current batch composition. For decode-only batches with known shapes, it replays the captured graph. For prefill or mixed batches, it falls back to eager mode. This hybrid approach provides the best of both worlds: flexibility for prefill and minimal overhead for decode.

### Performance Characteristics

**Throughput:** vLLM achieves 2-4x higher throughput than naive serving approaches on the same hardware. The V1 engine architecture delivers up to 24% better throughput for generation-heavy workloads compared to earlier vLLM versions.

**Latency:** Time to first token (TTFT) depends on prompt length and prefix cache hit rate. With APC enabled and warm caches, TTFT can be near-zero for repeated prefixes. Time per output token (TPOT) is primarily bounded by model size and GPU speed. Speculative decoding can reduce TPOT by 2-3x when the draft model has a high acceptance rate.

**Memory efficiency:** Near-zero KV cache fragmentation means vLLM can serve larger batches than competing systems on the same GPU. For a 13B model on an A100-80GB, vLLM can typically serve 2-3x more concurrent requests than systems using contiguous KV cache allocation.

**Scaling:** Linear throughput scaling with additional GPUs up to the point where communication overhead dominates. TP within a node typically scales well to 8 GPUs. PP across nodes adds latency per layer boundary but enables serving models that don't fit on one node.
