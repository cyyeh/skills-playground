## Core Concepts
<!-- level: beginner -->
<!-- references:
- [Fast and Expressive LLM Inference with RadixAttention and SGLang](https://www.lmsys.org/blog/2024-01-17-sglang/) | blog
- [SGLang Paper](https://arxiv.org/abs/2312.07104) | paper
- [Constrained Decoding in SGLang](https://deepwiki.com/sgl-project/sgl-learning-materials/3.3-constrained-decoding) | community
- [Mini-SGLang: Efficient Inference Engine in a Nutshell](https://www.lmsys.org/blog/2025-12-17-minisgl/) | blog
-->

### RadixAttention (KV Cache Reuse)

**RadixAttention** is SGLang's signature innovation for automatically reusing KV cache across multiple LLM calls. Think of it like a **library's catalog system**: instead of re-reading an entire book every time someone asks about a chapter, the library keeps an index (radix tree) of which pages have already been read and where they're stored. When a new request shares a prefix with a previous one, the system instantly finds the cached computation and picks up from where it left off.

In technical terms, SGLang organizes all cached key-value tensors in a [radix tree](https://www.lmsys.org/blog/2024-01-17-sglang/) data structure, where each path from root to leaf represents a sequence of tokens. When a new prompt arrives, the system walks the tree to find the longest matching prefix and reuses those cached KV pairs, skipping the expensive prefill computation for the shared portion. This is critical because in real-world workloads -- multi-turn chat, few-shot prompting, agentic tool use -- requests frequently share long common prefixes.

### Continuous Batching

**Continuous batching** is how SGLang keeps the GPU busy at all times. Imagine a **bus that never waits at the station** -- instead of waiting for all passengers to board before departing, new passengers hop on and completed passengers hop off while the bus keeps moving. In SGLang, the scheduler continuously adds new requests to the running batch as existing requests finish generating tokens, maximizing GPU utilization.

This contrasts with static batching where the system must wait for the slowest request in a batch to complete before processing any new ones. SGLang's scheduler runs a tight event loop that merges new prefill requests with ongoing decode operations every iteration.

### Chunked Prefill

**Chunked prefill** breaks long prompt processing into smaller pieces so the system can interleave prefill with ongoing decode work. It is like a **copy machine that processes large documents page by page** rather than feeding the entire stack at once -- this lets other people make quick copies between pages instead of waiting for the entire job to finish.

When a prompt is very long (thousands of tokens), processing it all at once would block the GPU and starve shorter requests. SGLang splits long prefills into configurable chunks and schedules them alongside decode steps, maintaining low latency for all concurrent requests.

### Constrained Decoding

**Constrained decoding** forces the model's output to follow a specific format or grammar, like JSON, regex patterns, or custom schemas. Think of it as **fill-in-the-blank with rules**: instead of letting someone write freely, you give them a form where certain fields must be numbers, others must be selected from a dropdown, and the overall structure must match a template.

SGLang implements this through grammar backends (primarily [XGrammar](https://github.com/mlc-ai/xgrammar)) that compile grammar specifications into efficient finite-state machines. At each decoding step, the backend generates a bitmask of valid tokens and applies it to the model's logits before sampling, ensuring every generated token is valid according to the grammar.

### Frontend Language (SGLang DSL)

The **SGLang frontend language** is a Python-embedded domain-specific language for writing structured LLM programs. It is like a **screenplay script with stage directions**: instead of just writing dialogue (prompts), you can direct actors to improvise within constraints, fork into parallel scenes, and reference earlier dialogue -- all in a natural scripting format.

Key primitives include `gen()` for generation, `select()` for constrained choices, `fork()` for parallel branching, and variable references for composing outputs. The frontend captures program structure that the backend runtime can exploit for optimization, such as identifying shared prefixes across forked branches.

### Speculative Decoding

**Speculative decoding** uses a smaller, faster "draft" model to predict multiple tokens ahead, then verifies them with the full model in a single forward pass. It is like a **secretary who drafts a letter for the CEO**: the secretary writes quickly, the CEO reviews and approves most of it in one pass, and only the rejected parts need rewriting. This trades a small amount of extra computation for significantly fewer slow forward passes.

SGLang supports [EAGLE](https://github.com/SafeAILab/EAGLE)-based speculative decoding, where the draft model shares embeddings and the language head with the target model, minimizing overhead while achieving 1.5-2x speedup on decode-heavy workloads.

### Tensor Parallelism

**Tensor parallelism** splits a single model across multiple GPUs so that each GPU handles a slice of every layer's computation. Think of a **team of carpenters building one table together**: instead of each carpenter building a separate table, they each work on different legs simultaneously, then assemble the final product. This enables serving models that are too large to fit in a single GPU's memory.

SGLang uses NCCL for inter-GPU communication and supports tensor parallelism across multiple GPUs on the same node, as well as pipeline parallelism and expert parallelism for MoE (Mixture of Experts) models.

### How They Fit Together

A typical SGLang deployment works as follows: a user writes an LLM program using the **frontend language** (or simply sends an OpenAI-compatible API request). The HTTP server passes the request to the **TokenizerManager**, which tokenizes it and forwards it to the **Scheduler**. The scheduler uses **RadixAttention** to check for cached prefixes, applies the **scheduling policy** (cache-aware or FCFS) to prioritize requests, and assembles a batch using **continuous batching** with **chunked prefill** for long prompts. The batch runs on the GPU (potentially across multiple GPUs via **tensor parallelism**), with **constrained decoding** enforcing output format and **speculative decoding** accelerating token generation. Generated tokens flow back through the detokenizer to the user.
