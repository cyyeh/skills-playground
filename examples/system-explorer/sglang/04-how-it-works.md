## How It Works
<!-- level: intermediate -->
<!-- references:
- [Fast and Expressive LLM Inference with RadixAttention and SGLang](https://www.lmsys.org/blog/2024-01-17-sglang/) | blog
- [SGLang Paper](https://arxiv.org/abs/2312.07104) | paper
- [Mini-SGLang: Efficient Inference Engine in a Nutshell](https://www.lmsys.org/blog/2025-12-17-minisgl/) | blog
- [SGLang Learning Series: RadixAttention](https://medium.com/@dharamendra1314.kumar/sglang-learning-series-part-1-shared-prefix-kv-cache-and-radixattention-d7a847d20b1f) | blog
-->

### The Radix Tree KV Cache

The heart of SGLang's performance is the [radix tree](https://www.lmsys.org/blog/2024-01-17-sglang/) data structure that manages KV cache. Here is how it works internally:

**Data Structure.** A radix tree (also called a Patricia trie) maps token sequences to GPU memory locations storing cached KV tensors. Unlike a standard trie where each edge represents a single token, a radix tree allows edges to carry variable-length sequences, making it more space-efficient. Each `TreeNode` stores: children (a dictionary mapping the first token of each edge to child nodes), a `key` (the token sequence on the edge from parent), a `value` (a tensor of GPU memory indices for the KV cache pages), a `lock_ref` counter (to prevent eviction of actively used entries), and timestamps for LRU eviction.

**Prefix Matching.** When a new request arrives with token sequence `[t1, t2, ..., tn]`, the `match_prefix()` method walks the tree from the root. At each node, it finds the child edge that shares the longest common prefix with the remaining tokens. It follows that edge and continues recursively until no further match is possible. The method returns the concatenated GPU memory indices for all matched KV cache pages and the last matched node (for later insertion).

**Insertion.** After processing a request, the `insert()` method adds the new token-to-KV-cache mappings back into the tree. If the sequence extends an existing path, it appends to the appropriate edge. If it diverges, it splits the edge at the divergence point and creates new child nodes.

**Eviction.** When GPU memory is full, the radix tree uses LRU (Least Recently Used) eviction by default, with support for FIFO, LFU, and priority-based strategies. Eviction starts from leaf nodes and recursively removes parents that become childless. Nodes with `lock_ref > 0` (actively used by running requests) are never evicted.

**Page-Aligned Storage.** KV cache is stored in fixed-size pages (configurable page size, default 1 token per page). Token sequences are aligned to page boundaries during matching and insertion, ensuring efficient memory management.

### The Scheduling Loop

The scheduler runs a tight event loop that orchestrates all runtime decisions:

**Event Loop (`event_loop_normal`).** Each iteration: (1) receive new requests from ZMQ, (2) process input requests (add to waiting queue), (3) call `get_next_batch_to_run()` to select the next batch, (4) run the batch on GPU, (5) process results (update request state, stream tokens back).

**Prefill vs Decode Priority.** The scheduler prioritizes new prefill requests over ongoing decode. This is because prefill is compute-bound (processes many tokens at once with high arithmetic intensity) while decode is memory-bandwidth-bound (generates one token at a time). Interleaving prefill into decode iterations keeps the GPU's compute units busy rather than leaving them idle during memory-bound decode steps.

**Batch Assembly.** The `PrefillAdder` class manages the token budget for each batch. It iterates through the waiting queue (ordered by the scheduling policy) and adds requests until the token budget is exhausted or memory constraints are hit. Each added request's prefix is matched against the RadixCache, and only the unmatched suffix needs actual prefill computation.

**Cache-Aware Scheduling.** When using the LPM (Longest Prefix Match) policy, the scheduler computes the prefix match length for each waiting request against the RadixCache, then sorts by descending match length. This means requests that can reuse the most cached computation are served first, maximizing effective throughput. When the waiting queue grows beyond 128 requests, the policy dynamically falls back to FCFS to avoid the O(n*m) overhead of prefix matching every request.

### Continuous Batching and Chunked Prefill

**Continuous Batching.** Unlike static batching where a batch is assembled once and processed until all requests complete, SGLang's continuous batching allows the composition of the running batch to change every iteration. Completed requests are removed and new requests are added without stalling. This is managed by the `ScheduleBatch` class which tracks the state of all in-flight requests.

**Chunked Prefill.** Long prompts are split into chunks (default chunk size is configurable). Each chunk is processed as a separate prefill step, interleaved with decode steps for other requests. This prevents a single long prompt from monopolizing the GPU. The scheduler tracks which requests are "chunked" (partially prefilled) and schedules their remaining chunks in subsequent iterations.

### Constrained Decoding via Grammar Backends

SGLang's constrained decoding works through a pluggable grammar backend architecture:

**Grammar Compilation.** When a request specifies a JSON schema, regex pattern, or EBNF grammar, the grammar backend compiles it into an internal representation. XGrammar (the default backend) compiles grammars into a set of token bitmasks indexed by automaton state -- essentially precomputing which tokens are valid at each position.

**Per-Step Masking.** At each decode step, the grammar backend provides a bitmask of valid next tokens based on the current automaton state. This bitmask is applied to the model's logits using efficient GPU operations (`apply_token_bitmask_inplace_triton` on NVIDIA or CUDA kernels on AMD), zeroing out invalid tokens before sampling. The automaton then transitions to the next state based on the sampled token.

**Jump-Forward Optimization.** When the grammar dictates that only one token sequence is valid (e.g., a required JSON key name), the system can "jump forward" by emitting those tokens directly without running the model, saving compute.

### Speculative Decoding (EAGLE)

SGLang supports EAGLE-based speculative decoding for accelerating auto-regressive generation:

**Draft Phase.** The EAGLE draft model (a lightweight model sharing the target's embeddings and language head) generates a tree of candidate continuations -- typically 3-5 tokens deep with multiple branches via top-k sampling. Each draft step is fast because the draft model is much smaller.

**Verification Phase.** The target model processes all candidate tokens in a single forward pass (batched as a tree). It computes logits for every candidate position simultaneously. Tokens where the draft model's prediction matches the target's distribution are accepted; the first mismatch point becomes the cutoff.

**Acceptance and Rollback.** Accepted tokens are committed to the output and their KV cache entries are retained. Rejected tokens and their KV cache entries are discarded. In practice, EAGLE achieves 60-80% acceptance rates, yielding 1.5-2x speedup on decode-heavy workloads.

### Performance Characteristics

**Throughput.** SGLang achieves approximately 16,200 tokens/second on H100 GPUs for typical workloads, compared to vLLM's 12,500 tokens/second with FlashInfer -- roughly a 30% advantage. On workloads with high prefix reuse (multi-turn chat, few-shot), the advantage can reach 2-5x due to RadixAttention.

**Latency.** SGLang maintains stable per-token latency of 4-21ms across varying concurrency levels. Time-to-first-token (TTFT) is competitive but not always the fastest -- vLLM can achieve lower TTFT on some workloads due to its C++ routing layer avoiding Python GIL contention.

**Memory Efficiency.** The radix tree enables sharing KV cache across requests with common prefixes, effectively increasing the usable batch size for a given GPU memory budget. This is particularly impactful for few-shot and system-prompt-heavy workloads where 50-90% of tokens may be shared.

**Scaling.** SGLang scales well with tensor parallelism across GPUs on a single node. For multi-node deployment, it supports data parallelism with a lightweight `DataParallelController`, as well as expert parallelism for MoE models and prefill/decode disaggregation for latency-sensitive deployments.
