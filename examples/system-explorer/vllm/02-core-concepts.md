## Core Concepts
<!-- level: beginner -->
<!-- references:
- [PagedAttention Paper](https://arxiv.org/abs/2309.06180) | paper
- [Inside vLLM: Anatomy of a High-Throughput LLM Inference System](https://blog.vllm.ai/2025/09/05/anatomy-of-vllm.html) | blog
- [vLLM Optimization and Tuning](https://docs.vllm.ai/en/stable/configuration/optimization/) | official-docs
-->

### PagedAttention

**PagedAttention** is vLLM's core innovation -- an attention algorithm that manages the KV cache using non-contiguous memory blocks, inspired by how operating systems manage virtual memory with paging.

**Analogy:** Think of a library where each book (a request's KV cache) doesn't need a single continuous shelf. Instead, chapters can be stored on any available shelf segment, and a catalog (block table) tracks which shelf holds which chapter. This means no shelf space goes unused just because a book doesn't fit in one contiguous spot.

**Why it matters:** Traditional LLM serving systems allocate one large contiguous chunk of GPU memory per request for the KV cache. If a request doesn't use all of that allocation, the remainder is wasted. If many requests arrive, the system runs out of memory even though plenty of fragmented space remains. PagedAttention breaks the KV cache into fixed-size blocks (typically 16 tokens each), maps them via a block table, and achieves near-zero memory waste -- under 4% fragmentation compared to 60-80% in naive systems.

### KV Cache

The **KV cache** (Key-Value cache) stores the intermediate attention states computed during text generation. Every token generated requires attending to all previous tokens, and the KV cache holds those computed key and value vectors so they don't need to be recomputed.

**Analogy:** Imagine you're writing a long essay and keeping running notes of everything you've already written so you don't have to re-read the entire essay every time you write the next sentence. The KV cache is those running notes -- they grow with each new token and can consume enormous amounts of GPU memory for long sequences.

**Why it matters:** For a 13B-parameter model, a single request's KV cache can consume hundreds of megabytes. With thousands of concurrent requests, efficient KV cache management is the single biggest lever for throughput. vLLM's block-based KV cache management is what enables its dramatic memory efficiency gains.

### Continuous Batching

**Continuous batching** (also called iteration-level scheduling) dynamically adds and removes requests from the running batch at every generation step, rather than waiting for an entire batch to finish before starting new requests.

**Analogy:** Consider a busy restaurant kitchen. Static batching is like waiting until all diners at one table finish eating before seating anyone new. Continuous batching is like seating new diners at any table the moment a seat opens -- the kitchen never stops cooking, and no seat sits idle.

**Why it matters:** In traditional static batching, a batch of 32 requests might have some finishing in 10 tokens and others in 500 tokens. The short requests hold their GPU memory hostage until the longest request finishes. Continuous batching frees those resources immediately, delivering 3-10x higher throughput on the same hardware by keeping the GPU fully utilized at all times.

### Tensor Parallelism

**Tensor parallelism** (TP) splits a single model's weight matrices across multiple GPUs so that each GPU holds a shard of every layer and they collectively compute each forward pass.

**Analogy:** Think of a team of chefs each responsible for one ingredient of every dish. Each chef works on their part simultaneously, they combine results at a specific handoff point, and together they produce the complete dish faster than any single chef could alone.

**Why it matters:** Many modern LLMs (70B+ parameters) don't fit on a single GPU. Tensor parallelism distributes the model across 2, 4, or 8 GPUs on the same node, keeping latency low because the inter-GPU communication within a node is fast (NVLink). vLLM makes this a one-flag configuration: `--tensor-parallel-size 4`.

### Pipeline Parallelism

**Pipeline parallelism** (PP) splits a model's layers across multiple GPUs (or nodes) so that each GPU holds a contiguous subset of layers and passes intermediate activations to the next GPU in sequence.

**Analogy:** An assembly line in a factory -- each station handles one phase of production, and items flow from station to station. While station 3 works on item A, station 2 can start on item B, and station 1 on item C. The pipeline stays full.

**Why it matters:** When you need to scale beyond one node (e.g., 8+ GPUs across machines), tensor parallelism's all-reduce communication becomes a bottleneck due to network latency. Pipeline parallelism lets you distribute layers across nodes where only point-to-point activation transfers are needed. vLLM supports PP combined with TP for large-scale deployments.

### Speculative Decoding

**Speculative decoding** uses a small, fast "draft" model to guess multiple tokens ahead, then verifies those guesses in a single forward pass of the larger "target" model, accepting correct guesses and discarding wrong ones.

**Analogy:** Like a junior associate drafting a legal brief and a senior partner reviewing it in one pass. If the draft is mostly right, the partner saves time. If parts are wrong, the partner corrects only those parts. Either way, it's faster than the partner writing every word themselves.

**Why it matters:** LLM generation is bottlenecked by the sequential nature of autoregressive decoding -- each token depends on the previous one. Speculative decoding breaks this bottleneck by allowing multiple tokens to be verified in parallel. vLLM supports several draft model strategies including [EAGLE](https://github.com/vllm-project/vllm/tree/main/vllm/v1/spec_decode/eagle.py), Medusa, and n-gram based proposers, reducing latency significantly for interactive workloads.

### Prefix Caching

**Prefix caching** (also called Automatic Prefix Caching or APC) reuses the KV cache of shared prompt prefixes across multiple requests, avoiding redundant computation.

**Analogy:** If a hundred students all start their essays with the same introduction paragraph, the teacher only needs to read that introduction once and reuse their notes about it for every student's essay.

**Why it matters:** In multi-turn chat, every follow-up message resends the entire conversation history as a prefix. In document Q&A, the same document is sent with every question. Without prefix caching, the system recomputes the KV cache for these shared prefixes every time. APC uses a hash-based lookup to detect shared prefixes and reuses their cached KV blocks, dramatically reducing prefill latency for these common workloads. Enable it with `--enable-prefix-caching`.

### CUDA Graphs

**CUDA graphs** are a GPU optimization that records a sequence of GPU operations (kernel launches, memory copies) once and replays them without the overhead of CPU-side launch coordination.

**Analogy:** Instead of a conductor calling out each instruction to the orchestra one by one at every performance, the entire performance is recorded once and then replayed from the recording -- every musician knows exactly what to do without waiting for each cue.

**Why it matters:** For small batch decode steps (which are very fast on the GPU), the CPU overhead of launching individual CUDA kernels can dominate total latency. CUDA graph capture records the entire forward pass once and replays it, reducing overhead by 10-30% for decode-heavy workloads.

### How They Fit Together

A request arrives at the vLLM server and enters the **continuous batching** scheduler. The scheduler checks if the request's prompt shares a **prefix** with cached entries (**prefix caching**). For the unique portion of the prompt, the scheduler allocates **KV cache** blocks using **PagedAttention**'s block table. The model forward pass runs across GPUs via **tensor parallelism** or **pipeline parallelism**, using **CUDA graphs** for efficient kernel execution during decode steps. If enabled, **speculative decoding** uses a draft model to propose multiple tokens per step, verifying them in batch to reduce latency. As requests complete, the scheduler immediately reclaims their KV cache blocks and admits new requests from the waiting queue -- keeping the GPU fully utilized at all times.
