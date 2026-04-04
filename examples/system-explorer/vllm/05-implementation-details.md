## Implementation Details
<!-- level: advanced -->
<!-- references:
- [vLLM Quickstart Guide](https://docs.vllm.ai/en/latest/) | official-docs
- [vLLM GitHub Source](https://github.com/vllm-project/vllm) | github
- [vLLM Production Stack](https://docs.vllm.ai/projects/production-stack/en/latest/deployment/) | official-docs
-->

### Getting Started

The fastest path from zero to running vLLM:

```bash
# Install vLLM (requires Python 3.9+ and CUDA 12.1+)
pip install vllm

# Start the OpenAI-compatible API server with a model
vllm serve meta-llama/Llama-3.1-8B-Instruct

# Or for a specific GPU configuration with tensor parallelism
vllm serve meta-llama/Llama-3.1-70B-Instruct \
  --tensor-parallel-size 4 \
  --enable-prefix-caching
```

Test it with a curl request:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

For offline batch inference in Python:

```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-3.1-8B-Instruct")
params = SamplingParams(temperature=0.7, top_p=0.9, max_tokens=256)

prompts = ["Explain quantum computing in simple terms.",
           "Write a haiku about distributed systems."]
outputs = llm.generate(prompts, params)

for output in outputs:
    print(output.outputs[0].text)
```

### Configuration Essentials

| Parameter | Default | What It Controls | When to Change |
|-----------|---------|-----------------|----------------|
| `--tensor-parallel-size` | 1 | Number of GPUs for tensor parallelism | Model doesn't fit on one GPU |
| `--pipeline-parallel-size` | 1 | Number of pipeline stages | Multi-node deployment |
| `--max-model-len` | Model's max | Maximum sequence length | Reduce to serve more concurrent requests |
| `--gpu-memory-utilization` | 0.9 | Fraction of GPU memory for KV cache | Lower if OOM during model loading |
| `--enable-prefix-caching` | False | Automatic prefix caching | Multi-turn chat, document Q&A |
| `--max-num-seqs` | 256 | Maximum concurrent sequences | Tune based on workload concurrency |
| `--block-size` | 16 | Tokens per KV cache block | Rarely needs changing |
| `--speculative-model` | None | Draft model for speculative decoding | Latency-sensitive workloads |
| `--num-speculative-tokens` | None | Draft tokens per step | Balance acceptance rate vs. overhead |
| `--quantization` | None | Weight quantization (awq, gptq, fp8) | Reduce memory, serve larger models |

### Code Patterns

**Streaming completions with the OpenAI client:**

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="unused")

stream = client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct",
    messages=[{"role": "user", "content": "Explain PagedAttention"}],
    stream=True,
    max_tokens=512,
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

**Guided/structured generation with JSON schema:**

```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-3.1-8B-Instruct")

schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "city": {"type": "string"}
    },
    "required": ["name", "age", "city"]
}

params = SamplingParams(
    temperature=0.0,
    max_tokens=100,
    guided_decoding={"json": schema}
)

output = llm.generate(["Extract: John is 30, lives in SF"], params)
```

### Source Code Walkthrough

#### PagedAttention -- Block Pool Implementation

The `BlockPool` class is the memory allocator at the heart of PagedAttention. It manages a pool of fixed-size KV cache blocks using a doubly-linked free list and a hash table for prefix cache lookups. This implements the PagedAttention concept from Core Concepts -- the block-based, non-contiguous memory allocation that eliminates KV cache fragmentation.

```python
# source: vllm/v1/core/block_pool.py:1-55
# github: vllm-project/vllm
# tag: v0.19.0
class BlockPool:
    """Pool of KV cache blocks with prefix caching support.

    Manages fixed-size blocks that store KV tensors for PagedAttention.
    Uses a free block queue (doubly-linked list) for O(1) allocation
    and a hash table (BlockHashToBlockMap) for prefix cache lookups.
    """

    def __init__(
        self,
        num_gpu_blocks: int,
        enable_caching: bool,
        hash_block_size: int,
        use_eagle: bool = False,
        enable_kv_cache_events: bool = False,
        log_stats: bool = False,
    ) -> None:
        self.num_gpu_blocks = num_gpu_blocks
        self.enable_caching = enable_caching
        self.hash_block_size = hash_block_size

        # All KV cache blocks -- one per physical GPU block
        self.blocks: list[KVCacheBlock] = [
            KVCacheBlock(block_id=i) for i in range(num_gpu_blocks)
        ]

        # Free block queue: doubly-linked list for O(1) alloc/free
        self.free_block_queue = FreeKVCacheBlockQueue(self.blocks)

        # Hash table for prefix cache lookups
        self.cached_block_hash_to_block = BlockHashToBlockMap()

        # Null block: reserved placeholder (block_id=0)
        self.null_block = self.blocks[0]
        self.null_block.ref_cnt = 1  # Never evict
```

#### KV Cache Manager -- Block Allocation

The `KVCacheManager` sits above the BlockPool and handles the complex logic of allocating KV cache blocks for each request, integrating with the prefix cache, and managing block lifecycles. This implements the KV Cache concept from Core Concepts -- coordinating block allocation across requests with prefix awareness.

```python
# source: vllm/v1/core/kv_cache_manager.py:104-160
# github: vllm-project/vllm
# tag: v0.19.0
class KVCacheManager:
    """Manages KV cache block allocation across all requests.

    Coordinates between the BlockPool (physical allocation),
    prefix cache (hash-based reuse), and per-request block tables.
    """

    def __init__(
        self,
        kv_cache_config: KVCacheConfig,
        max_model_len: int,
        hash_block_size: int,
        enable_caching: bool = True,
        use_eagle: bool = False,
        log_stats: bool = False,
        enable_kv_cache_events: bool = False,
        dcp_world_size: int = 1,
        pcp_world_size: int = 1,
        metrics_collector: KVCacheMetricsCollector | None = None,
    ) -> None:
        # Pre-construct empty KVCacheBlocks to minimize GC overhead
        self.req_to_blocks: dict[str, KVCacheBlocks] = {}
        self.coordinator = KVCacheCoordinator(
            kv_cache_config=kv_cache_config,
            max_model_len=max_model_len,
            hash_block_size=hash_block_size,
            enable_caching=enable_caching,
            # ...
        )
```

#### KV Cache Manager -- allocate_slots Method

The `allocate_slots` method is where PagedAttention's block allocation happens on each scheduling step. It handles prefix matching, sliding window considerations, and block-level allocation for new tokens.

```python
# source: vllm/v1/core/kv_cache_manager.py:210-280
# github: vllm-project/vllm
# tag: v0.19.0
def allocate_slots(
    self,
    request: Request,
    num_new_tokens: int,
    num_new_blocks: int,
    new_computed_blocks: Optional[list[KVCacheBlock]] = None,
    num_draft_tokens: int = 0,
) -> Optional[KVCacheBlocks]:
    """Allocate KV cache blocks for new tokens in a request.

    Three-stage process:
    1. Free unnecessary blocks and validate free block count
    2. Handle prefix tokens with sliding window consideration
    3. Allocate new blocks for tokens requiring computation

    Accommodates asynchronous KV data loading and handles both
    verified and unverified draft tokens -- caching only finalized tokens.
    """
    # Stage 1: Ensure sufficient free blocks
    blocks = self.coordinator.allocate_slots(
        request_id=request.request_id,
        num_new_tokens=num_new_tokens,
        num_new_blocks=num_new_blocks,
        new_computed_blocks=new_computed_blocks,
        num_draft_tokens=num_draft_tokens,
    )
    return blocks
```

#### Continuous Batching -- Scheduler Core

The `Scheduler` class implements continuous batching by maintaining separate queues for running and waiting requests, promoting requests at every step. This implements the Continuous Batching concept from Core Concepts.

```python
# source: vllm/v1/core/sched/scheduler.py:74-140
# github: vllm-project/vllm
# tag: v0.19.0
class Scheduler:
    """Continuous batching scheduler for vLLM V1 engine.

    Maintains a waiting queue and running list. At each step:
    1. Process running requests (allocate KV blocks for new tokens)
    2. Preempt if KV cache is exhausted
    3. Promote waiting requests when resources permit
    """

    def __init__(
        self,
        scheduler_config: SchedulerConfig,
        model_config: ModelConfig,
        kv_cache_config: KVCacheConfig,
        # ... additional configs
    ) -> None:
        # Request queues: waiting and running
        self.waiting = create_request_queue(self.policy)
        self.skipped_waiting = create_request_queue(self.policy)
        self.running: list[Request] = []

        # Resource constraints
        self.max_num_running_reqs = scheduler_config.max_num_seqs
        self.max_num_scheduled_tokens = (
            scheduler_config.max_num_batched_tokens
        )

        # KV cache manager for block allocation
        self.kv_cache_manager = KVCacheManager(
            kv_cache_config=kv_cache_config,
            max_model_len=model_config.max_model_len,
            enable_caching=cache_config.enable_prefix_caching,
            # ...
        )
```

#### Continuous Batching -- Schedule Loop

The `schedule()` method is the heart of continuous batching. It runs on every engine step and decides which requests to execute, balancing token budget and KV cache capacity.

```python
# source: vllm/v1/core/sched/scheduler.py:271-380
# github: vllm-project/vllm
# tag: v0.19.0
def schedule(self) -> SchedulerOutput:
    """Run one scheduling step.

    Phase 1: Schedule running requests
    - Allocate KV blocks for each running request's new tokens
    - Preempt lowest-priority requests if cache exhausted

    Phase 2: Schedule waiting requests
    - Check max concurrent requests limit
    - Process prefix cache hits
    - Allocate blocks for new requests
    - Move from waiting to running on success
    """
    token_budget = self.max_num_scheduled_tokens

    # Phase 1: Process running requests
    for request in self.running:
        num_new_tokens = request.num_tokens - request.num_computed_tokens
        blocks = self.kv_cache_manager.allocate_slots(
            request, num_new_tokens, num_new_blocks
        )
        if blocks is None:
            # KV cache full -- preempt this request
            self._preempt_request(request)
            continue
        token_budget -= num_new_tokens

    # Phase 2: Promote waiting requests
    while self.waiting and len(self.running) < self.max_num_running_reqs:
        request = self.waiting.peek()
        if not self.kv_cache_manager.can_fit_full_sequence(request):
            break
        request = self.waiting.pop()
        self.running.append(request)
        token_budget -= request.num_prefill_tokens
```

#### Tensor Parallelism -- Multi-Process Executor

The `MultiprocExecutor` manages multi-GPU execution by spawning worker processes and communicating via shared-memory message queues. This implements the Tensor Parallelism concept from Core Concepts.

```python
# source: vllm/v1/executor/multiproc_executor.py:103-180
# github: vllm-project/vllm
# tag: v0.19.0
class MultiprocExecutor(Executor):
    """Multi-GPU executor using one process per GPU rank.

    Spawns worker processes, establishes shared-memory message queues,
    and dispatches model execution via collective RPC.
    Supports tensor parallelism (TP) and pipeline parallelism (PP).
    """
    supports_pp: bool = True

    def __init__(self, vllm_config, monitor_workers: bool = True):
        # Determine parallelism configuration
        tp_size, pp_size, pcp_size = self._get_parallel_sizes()
        assert self.world_size == tp_size * pp_size * pcp_size

        # Create shared-memory broadcast queue for scheduler outputs
        self.rpc_broadcast_mq = MessageQueue(tp_size * pp_size * pcp_size)

        # Spawn one worker process per GPU rank
        for rank in range(self.local_world_size):
            worker = WorkerProc.make_worker_process(
                vllm_config=vllm_config,
                local_rank=rank,
                rank=rank,
                distributed_init_method=self.distributed_init_method,
                rpc_broadcast_mq=self.rpc_broadcast_mq,
            )
            self.workers.append(worker)
```

#### Tensor Parallelism -- Execute Model Dispatch

The `execute_model` method dispatches forward pass execution to all GPU workers via collective RPC, collecting results from the designated output rank.

```python
# source: vllm/v1/executor/multiproc_executor.py:331-413
# github: vllm-project/vllm
# tag: v0.19.0
def execute_model(
    self,
    scheduler_output: SchedulerOutput,
    non_block: bool = False,
) -> ModelRunnerOutput | None | Future[ModelRunnerOutput | None]:
    """Dispatch model execution to all GPU workers.

    Broadcasts scheduler output to all ranks via shared-memory MQ.
    Collects results from the output rank (TP rank 0, last PP stage).
    Supports non-blocking execution for pipeline parallelism.
    """
    return self.collective_rpc(
        "execute_model",
        args=(scheduler_output,),
        unique_reply_rank=self.output_rank,
        non_block=non_block,
    )
```

#### Speculative Decoding -- EAGLE Proposer

The EAGLE proposer generates draft tokens using the target model's hidden states. This implements the Speculative Decoding concept from Core Concepts.

```python
# source: vllm/v1/spec_decode/eagle.py:45-120
# github: vllm-project/vllm
# tag: v0.19.0
class SpecDecodeBaseProposer:
    """Draft token proposer for EAGLE speculative decoding.

    Uses the target model's hidden states to predict future tokens
    via a lightweight draft head. Generates k candidate tokens that
    the target model verifies in a single forward pass.
    """

    def __init__(
        self,
        vllm_config: VllmConfig,
        device: torch.device,
        pass_hidden_states_to_model: bool,
        runner=None,
    ):
        self.num_speculative_tokens = (
            vllm_config.speculative_config.num_speculative_tokens
        )
        # Persistent GPU buffers for draft tokens
        self.draft_token_ids: torch.Tensor = None
        self.draft_positions: torch.Tensor = None
        self.draft_hidden_states: torch.Tensor = None

    def _greedy_sample(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """Greedy-sample draft tokens from hidden states."""
        if self.use_local_argmax_reduction:
            return self.model.get_top_tokens(hidden_states)
        return self.model.compute_logits(hidden_states).argmax(dim=-1)
```

#### Speculative Decoding -- Propose Method

The `propose()` method generates multiple draft tokens iteratively, using each predicted token's hidden state to predict the next.

```python
# source: vllm/v1/spec_decode/eagle.py:359-460
# github: vllm-project/vllm
# tag: v0.19.0
def propose(
    self,
    target_token_ids: torch.Tensor,
    target_positions: torch.Tensor,
    target_hidden_states: torch.Tensor,
    next_token_ids: torch.Tensor,
    token_indices_to_sample: torch.Tensor | None,
    common_attn_metadata: CommonAttentionMetadata,
    sampling_metadata: SamplingMetadata,
) -> torch.Tensor:
    """Generate draft token proposals.

    1. Prepare inputs from target model's hidden states
    2. Run draft model forward pass
    3. Greedy-sample first draft token
    4. Iteratively generate remaining speculative tokens
    """
    # First pass: prepare inputs and run draft model
    self.set_inputs_first_pass(
        target_token_ids, target_positions,
        target_hidden_states, next_token_ids
    )
    attn_metadata = self.build_per_group_and_layer_attn_metadata(
        common_attn_metadata
    )
    # Run draft model and sample
    hidden_states = self.model.forward(
        self.draft_token_ids, self.draft_positions, attn_metadata
    )
    draft_tokens = self._greedy_sample(hidden_states)

    # Iteratively generate remaining speculative tokens
    for i in range(1, self.num_speculative_tokens):
        self.set_inputs_subsequent_pass(draft_tokens, i)
        hidden_states = self.model.forward(
            self.draft_token_ids, self.draft_positions, attn_metadata
        )
        draft_tokens = self._greedy_sample(hidden_states)

    return self.draft_token_ids
```

#### Prefix Caching -- Hash-Based Block Lookup

The KV cache manager uses hash-based lookups to detect reusable prefix blocks. This implements the Prefix Caching concept from Core Concepts.

```python
# source: vllm/v1/core/kv_cache_manager.py:168-199
# github: vllm-project/vllm
# tag: v0.19.0
def get_computed_blocks(
    self,
    request: Request,
) -> tuple[list[KVCacheBlock], int]:
    """Find cached KV blocks that match the request's prefix.

    Uses hash-based lookup: the request's prompt tokens are hashed
    in block-sized chunks (16 tokens each). Each hash is looked up
    in the BlockPool's hash table. Matching blocks are reused
    (reference count incremented) instead of being recomputed.

    Returns the list of cached blocks and the number of
    computed tokens they cover.
    """
    computed_blocks = self.coordinator.get_computed_blocks(
        request_id=request.request_id,
        block_hashes=request.block_hashes,
    )
    # Touch cached blocks to prevent eviction
    for block in computed_blocks:
        self.coordinator.block_pool.touch(block)
    num_computed_tokens = len(computed_blocks) * self.hash_block_size
    return computed_blocks, num_computed_tokens
```

#### Engine Core -- The Main Loop

The `EngineCore.step()` method orchestrates one iteration of the inference engine, connecting the scheduler to the model executor. This implements the complete request processing pipeline described in Architecture.

```python
# source: vllm/v1/engine/core.py:281-313
# github: vllm-project/vllm
# tag: v0.19.0
def step(self) -> EngineCoreOutputs:
    """Execute one iteration of the engine loop.

    Coordinates: scheduler -> executor -> sampler -> output
    1. Check for unfinished requests
    2. Schedule the next batch
    3. Execute model forward pass (async)
    4. Get grammar bitmask for structured output
    5. Wait for model output
    6. Sample tokens from logits
    7. Update scheduler with results
    """
    if not self.scheduler.has_requests():
        return EngineCoreOutputs.empty()

    scheduler_output = self.scheduler.schedule()
    executor_output_future = self.model_executor.execute_model(
        scheduler_output, non_block=True
    )
    grammar_bitmask = self.scheduler.get_grammar_bitmask()

    model_output = executor_output_future.result()
    if model_output is None:
        sampled = self.model_executor.sample(grammar_bitmask)
    else:
        sampled = model_output

    self._process_aborts_queue()
    outputs = self.scheduler.update_from_output(sampled)
    return outputs
```

#### CUDA Graphs -- GPU Worker Execution

The GPU Worker's `execute_model` method shows how forward passes run with pipeline parallelism support, demonstrating the CUDA Graphs concept in action through the model runner's dispatch mechanism.

```python
# source: vllm/v1/worker/gpu_worker.py:614-685
# github: vllm-project/vllm
# tag: v0.19.0
@torch.inference_mode()
def execute_model(
    self, scheduler_output: "SchedulerOutput"
) -> ModelRunnerOutput | AsyncModelRunnerOutput | None:
    """Execute a model forward pass on this GPU.

    For pipeline parallelism:
    1. Wait for pending sends to complete
    2. Receive intermediate tensors from previous stage
    3. Execute model (eager or CUDA graph, per CUDAGraphDispatcher)
    4. Send intermediate tensors to next stage (non-blocking)

    The model runner internally selects between eager mode and
    CUDA graph replay based on the batch composition.
    """
    # Wait for previous pipeline sends
    if self.pipeline_parallel_size > 1:
        self._wait_for_pending_sends()

    # Receive from previous pipeline stage
    intermediate_tensors = self._recv_from_prev_stage()

    # Execute model forward pass
    output = self.model_runner.execute_model(
        scheduler_output,
        intermediate_tensors=intermediate_tensors,
    )

    # Send to next pipeline stage (non-blocking)
    if self.pipeline_parallel_size > 1:
        self._send_to_next_stage(output)

    return output
```

### Deployment Considerations

**GPU sizing:** A rule of thumb is that model weights consume approximately 2 bytes per parameter in FP16. A 70B model needs ~140GB, requiring at least 2 x A100-80GB with TP=2. KV cache memory comes from the remaining GPU memory after model weights are loaded.

**Monitoring:** vLLM exposes Prometheus metrics at `/metrics` including `vllm:num_requests_running`, `vllm:num_requests_waiting`, `vllm:gpu_cache_usage_perc`, and `vllm:avg_generation_throughput_toks_per_s`. Monitor `gpu_cache_usage_perc` -- when it consistently hits 100%, you need more GPU memory or should reduce `max-model-len`.

**Production stack:** The [vLLM Production Stack](https://github.com/vllm-project/production-stack) provides Helm charts for Kubernetes deployment with autoscaling, health checks, and prefix-aware request routing across multiple vLLM replicas.

**Quantization:** For memory-constrained deployments, vLLM supports AWQ, GPTQ, and FP8 quantization. Use `--quantization awq` with a pre-quantized model to reduce memory by ~50% with minimal quality loss.

**Upgrade path:** vLLM releases frequently (approximately every 2 weeks). Pin your version in production and test upgrades in staging. The V1 engine is the current recommended architecture -- the V0 engine is being phased out.
