## Common Q&A
<!-- level: all -->
<!-- references:
- [SGLang Official Documentation](https://sgl-project.github.io/) | official-docs
- [SGLang vs vLLM Comparison](https://www.gpu-mart.com/blog/sglang-vs-vllm) | blog
- [vLLM vs SGLang Performance Benchmark on Dual H100 GPUs](https://rawlinson.ca/articles/vllm-vs-sglang-performance-benchmark-h100) | blog
-->

### Q: What happens to the KV cache when GPU memory runs out?

When the KV cache fills GPU memory, the RadixCache eviction policy activates. By default, it uses LRU (Least Recently Used) eviction, starting from leaf nodes of the radix tree. Nodes with `lock_ref > 0` (actively used by running requests) are protected from eviction. The eviction is recursive: when a leaf node is removed and its parent becomes childless, the parent is also eligible for eviction. SGLang also supports FIFO, LFU, and priority-based eviction strategies via configuration. If eviction alone isn't sufficient, the scheduler will preempt lower-priority running requests, saving their partial state and re-adding them to the waiting queue.

### Q: How does SGLang handle requests that share different-length prefixes -- does it match greedily?

Yes, `match_prefix()` performs a greedy longest-prefix match. It walks the radix tree from the root, following the child edge that matches the most tokens at each level. The result is the longest contiguous prefix found in the cache. If two requests share tokens 1-100 but diverge at token 101, only the shared 1-100 portion is reused. Importantly, the match is page-aligned (configurable page size) -- if the match falls in the middle of a page, it rounds down to the nearest page boundary to maintain memory alignment.

### Q: When should I choose SGLang over vLLM?

Choose SGLang when: (1) your workload has significant prefix sharing (multi-turn chat, shared system prompts, few-shot); (2) you need structured/constrained output (JSON, code); (3) you're building agentic workflows with branching logic that benefit from the SGLang frontend language; (4) you need day-0 support for the latest open models. Choose vLLM when: (1) you need absolute lowest TTFT on single-shot requests; (2) your workload is mostly unique prompts with no prefix reuse; (3) you need features specific to vLLM's ecosystem (e.g., certain quantization methods or pipeline parallelism configurations). In benchmarks, SGLang typically wins on throughput (16,200 vs 12,500 tokens/sec on H100) while vLLM can win on TTFT under high concurrency.

### Q: Can I serve multiple models on a single SGLang instance?

Not in the traditional sense -- each SGLang server instance serves one base model. However, you can serve multiple LoRA adapters on top of a single base model, with dynamic adapter switching per request. For multi-model serving, run multiple SGLang instances and use a router (SGLang Router, NGINX, or Kubernetes Ingress) to direct requests to the appropriate instance.

### Q: What is the cache-aware scheduling policy and when does it fall back?

The default LPM (Longest Prefix Match) policy computes the prefix match length for each waiting request against the RadixCache, then sorts requests by descending match length. This means requests that can reuse the most cached computation are served first. However, computing prefix matches for every waiting request has O(n*m) complexity. When the waiting queue exceeds 128 requests, the policy automatically falls back to FCFS (First Come First Served) to avoid this overhead. You can force FCFS with `--schedule-policy fcfs` if your workload doesn't benefit from cache-aware scheduling.

### Q: How do I diagnose slow TTFT in production?

Start by checking: (1) `sglang_cache_hit_rate` -- low hit rates mean most requests require full prefill; (2) `sglang_num_waiting_requests` -- a growing waiting queue means the scheduler can't keep up; (3) `sglang_chunked_prefill_size` -- if set too large, long prefills block shorter requests; (4) GPU utilization via `nvidia-smi` -- if GPU is underutilized, the bottleneck is likely CPU-side (tokenization, scheduling). Consider reducing `--chunked-prefill-size` to interleave prefill with decode more aggressively, or increasing `--dp-size` to add more scheduler instances.

### Q: Does SGLang support streaming output?

Yes, SGLang supports streaming via Server-Sent Events (SSE) on the OpenAI-compatible API. Set `"stream": true` in your request and tokens are streamed back as they are generated. Internally, the detokenizer manager converts token IDs to text incrementally and sends each chunk back through the HTTP response. For the SGLang frontend language, streaming is handled through async generators in the `run()` method.

### Q: How does constrained decoding affect throughput?

Grammar-guided generation adds overhead at each decoding step for bitmask computation and application. With XGrammar (the default), the overhead is typically 5-15% throughput reduction depending on grammar complexity. Simple grammars (JSON with fixed schema) are near-free because the bitmask can be precomputed. Complex grammars (deeply nested structures, recursive patterns) require per-step automaton transitions that add latency. The jump-forward optimization partially mitigates this by skipping model calls when the grammar dictates a deterministic token sequence.
