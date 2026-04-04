## Implementation Details
<!-- level: advanced -->
<!-- references:
- [SGLang Official Documentation](https://sgl-project.github.io/) | official-docs
- [SGLang GitHub Repository](https://github.com/sgl-project/sglang) | github
- [SGLang Getting Started Guide](https://sgl-project.github.io/start/install.html) | tutorial
- [Serving SGLang: Launch a Production-Style Server](https://learnopencv.com/sglang-a-production-server/) | tutorial
-->

### Getting Started

The fastest way to get SGLang running is via pip:

```bash
# Install SGLang with all dependencies
pip install "sglang[all]"

# Or install with specific backend
pip install "sglang[all]" --find-links https://flashinfer.ai/whl/cu124/torch2.5/flashinfer-python

# Launch a server with Llama 3.1 8B
python -m sglang.launch_server --model-path meta-llama/Llama-3.1-8B-Instruct --port 30000

# Or use Docker
docker run --gpus all -p 30000:30000 \
  lmsys/sglang:latest \
  python -m sglang.launch_server --model-path meta-llama/Llama-3.1-8B-Instruct --host 0.0.0.0
```

Once the server is running, query it using the OpenAI-compatible API:

```bash
curl http://localhost:30000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7
  }'
```

### Configuration Essentials

| Parameter | Default | Description | When to Change |
|-----------|---------|-------------|----------------|
| `--tp-size` | 1 | Number of GPUs for tensor parallelism | Model doesn't fit on one GPU |
| `--mem-fraction-static` | 0.88 | Fraction of GPU memory for KV cache | OOM errors or need more cache |
| `--chunked-prefill-size` | 8192 | Max tokens per prefill chunk | Long prompts causing latency spikes |
| `--schedule-policy` | `lpm` | Scheduling policy (lpm, fcfs, dfs-weight) | Workloads without shared prefixes |
| `--max-running-requests` | auto | Max concurrent requests | Control memory usage |
| `--grammar-backend` | `xgrammar` | Constrained decoding backend | Need specific grammar features |
| `--quantization` | None | Quantization method (fp8, int4, awq, gptq) | Reduce memory, trade accuracy |
| `--enable-torch-compile` | False | Use torch.compile for model | Improve throughput on supported models |
| `--speculative-algorithm` | None | Speculative decoding (EAGLE) | Reduce decode latency |
| `--disable-radix-cache` | False | Disable KV cache reuse | Debugging or benchmarking |

### Code Patterns

**OpenAI-compatible client usage:**

```python
import openai

client = openai.Client(base_url="http://localhost:30000/v1", api_key="none")

response = client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct",
    messages=[{"role": "user", "content": "Explain RadixAttention briefly."}],
    temperature=0.7,
    max_tokens=256,
)
print(response.choices[0].message.content)
```

**Structured output with JSON schema:**

```python
import json

response = client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct",
    messages=[{"role": "user", "content": "Give me info about Paris."}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "city_info",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "country": {"type": "string"},
                    "population": {"type": "integer"}
                },
                "required": ["name", "country", "population"]
            }
        }
    }
)
info = json.loads(response.choices[0].message.content)
```

**SGLang frontend language:**

```python
import sglang as sgl

@sgl.function
def multi_turn_qa(s, question1, question2):
    s += sgl.user(question1)
    s += sgl.assistant(sgl.gen("answer1", max_tokens=256))
    s += sgl.user(question2)
    s += sgl.assistant(sgl.gen("answer2", max_tokens=256))

state = multi_turn_qa.run(
    question1="What is SGLang?",
    question2="How does RadixAttention work?",
)
print(state["answer1"])
print(state["answer2"])
```

### Source Code Walkthrough

#### RadixAttention -- Implementation

This is the core data structure that implements the RadixAttention concept from Core Concepts. The `TreeNode` class is the building block of the radix tree, storing KV cache references and LRU metadata for each prefix in the tree.

```python
# source: python/sglang/srt/mem_cache/radix_cache.py:78-130
# github: sgl-project/sglang
# tag: v0.5.9
class RadixKey:
    def __init__(
        self,
        token_ids: List[int],
        extra_key: Optional[str] = None,
        is_bigram: bool = False,
    ):
        self.token_ids = token_ids
        self.extra_key = extra_key
        self.is_bigram = is_bigram

    def __len__(self) -> int:
        return len(self.token_ids)

    def __getitem__(self, idx: Union[int, slice]) -> "RadixKey":
        if isinstance(idx, slice):
            return RadixKey(self.token_ids[idx], self.extra_key)
        return RadixKey([self.token_ids[idx]], self.extra_key)


class TreeNode:
    counter = 0

    def __init__(self, id: Optional[int] = None, priority: int = 0):
        self.children = defaultdict(TreeNode)
        self.parent: TreeNode = None
        self.key: RadixKey = None
        self.value: Optional[torch.Tensor] = None
        self.lock_ref = 0
        self.last_access_time = time.monotonic()
        self.creation_time = time.monotonic()
        self.hit_count = 0
        self.host_ref_counter = 0
        self.host_value: Optional[torch.Tensor] = None
        self.hash_value: Optional[List[str]] = None
        self.priority = priority
        self.id = TreeNode.counter if id is None else id
        TreeNode.counter += 1
```

The `RadixCache.match_prefix()` method performs the actual prefix matching -- walking the tree to find the longest cached prefix. This implements the "library catalog lookup" described in Core Concepts.

```python
# source: python/sglang/srt/mem_cache/radix_cache.py:200-245
# github: sgl-project/sglang
# tag: v0.5.9
def match_prefix(self, params: MatchPrefixParams) -> MatchResult:
    """Find the longest cached prefix of key in the radix tree."""
    key = params.key
    key, _ = self.maybe_bigram_convert(key)

    def empty_match_result():
        return MatchResult(
            device_indices=torch.empty(
                (0,), dtype=torch.int64, device=self.device,
            ),
            last_device_node=self.root_node,
            last_host_node=self.root_node,
        )

    if self.disable or len(key) == 0:
        return empty_match_result()

    if self.page_size != 1:
        page_aligned_len = len(key) // self.page_size * self.page_size
        key = key[:page_aligned_len]

    if len(key) == 0:
        return empty_match_result()

    value, last_node = self._match_prefix_helper(self.root_node, key)
    if value:
        value = torch.cat(value)
    else:
        value = torch.empty((0,), dtype=torch.int64, device=self.device)
    return MatchResult(
        device_indices=value,
        last_device_node=last_node,
        last_host_node=last_node,
    )
```

#### Continuous Batching -- Scheduler Event Loop

This implements the continuous batching concept. The `event_loop_normal` method is the scheduler's main loop -- it runs continuously, pulling in new requests, assembling batches, and dispatching GPU work without ever stopping.

```python
# source: python/sglang/srt/managers/scheduler.py:350-380
# github: sgl-project/sglang
# tag: v0.5.9
@DynamicGradMode()
def event_loop_normal(self):
    """A normal scheduler loop."""
    while True:
        # Receive requests
        recv_reqs = self.recv_requests()
        self.process_input_requests(recv_reqs)
        if self._engine_paused:
            self.cancel_bubble_timer()
            continue

        # Get the next batch to run
        batch = self.get_next_batch_to_run()
        self.cur_batch = batch

        # Launch the current batch
        if batch:
            result = self.run_batch(batch)
            self.process_batch_result(batch, result)
        else:
            self.self_check_during_idle()

        self.last_batch = batch
```

#### Continuous Batching -- Batch Assembly

The `get_next_batch_to_run` method decides whether to run prefill or decode at each step. This is where the "bus that never waits" logic lives -- merging finished chunks, prioritizing new prefills, and falling back to decode.

```python
# source: python/sglang/srt/managers/scheduler.py:400-440
# github: sgl-project/sglang
# tag: v0.5.9
def get_next_batch_to_run(self) -> Optional[ScheduleBatch]:
    self._abort_on_waiting_timeout()
    self._abort_on_running_timeout()

    chunked_req_to_exclude = set()

    # Merge finished requests from last batch into running batch
    if self.last_batch and self.last_batch.forward_mode.is_extend():
        self.last_batch.filter_batch(
            chunked_req_to_exclude=list(chunked_req_to_exclude)
        )
        if not self.last_batch.is_empty():
            self.running_batch.merge_batch(self.last_batch)

    # Get new prefill batch
    new_batch = self.get_new_batch_prefill()

    if new_batch is not None:
        ret = new_batch  # Prioritize prefill
    else:
        if (not self.running_batch.is_empty()
                and not self.running_batch.is_prefill_only):
            self.running_batch = self.update_running_batch(
                self.running_batch
            )
            ret = (self.running_batch
                   if not self.running_batch.is_empty() else None)
        else:
            ret = None

    return ret
```

#### Cache-Aware Scheduling Policy -- Implementation

This implements the scheduling policy concept described in Architecture. The `calc_priority` method reorders the waiting queue based on cache awareness -- specifically, the Longest Prefix Match policy sorts requests by how much KV cache they can reuse.

```python
# source: python/sglang/srt/managers/schedule_policy.py:50-95
# github: sgl-project/sglang
# tag: v0.5.9
class CacheAwarePolicy(Enum):
    """Scheduling policies that are tree cache-aware."""
    LPM = "lpm"       # longest prefix match
    DFS_WEIGHT = "dfs-weight"  # depth-first search weighting

class CacheAgnosticPolicy(Enum):
    """Scheduling policies independent of tree cache."""
    FCFS = "fcfs"      # first come first serve
    LOF = "lof"        # longest output first
    RANDOM = "random"
    ROUTING_KEY = "routing-key"

# In SchedulePolicy class:
def calc_priority(
    self, waiting_queue: List[Req],
    running_batch: Optional[ScheduleBatch] = None
) -> bool:
    if self.policy == CacheAgnosticPolicy.FCFS:
        if self.enable_priority_scheduling:
            SchedulePolicy._sort_by_priority_and_fcfs(
                waiting_queue, self.priority_sign
            )
        return False

    policy = self._determine_active_policy(waiting_queue)
    prefix_computed = False

    if isinstance(policy, CacheAwarePolicy):
        prefix_computed = True
        temporary_deprioritized = self._compute_prefix_matches(
            waiting_queue, policy
        )
        if policy == CacheAwarePolicy.LPM:
            SchedulePolicy._sort_by_longest_prefix(
                waiting_queue, temporary_deprioritized
            )
```

#### Constrained Decoding -- XGrammar Backend

This implements the constrained decoding concept. The `XGrammarGrammarBackend` compiles grammar specifications into token bitmasks. The `apply_vocab_mask` method is called at every decoding step to zero out tokens that violate the grammar.

```python
# source: python/sglang/srt/constrained/xgrammar_backend.py:30-80
# github: sgl-project/sglang
# tag: v0.5.9
class XGrammarGrammarBackend(BaseGrammarBackend):
    def __init__(
        self,
        tokenizer,
        vocab_size: int,
        model_eos_token_ids: Optional[List[int]] = None,
        any_whitespace: bool = True,
    ):
        super().__init__()

        if hasattr(tokenizer, "init_xgrammar"):
            tokenizer_info, override_stop_tokens = (
                tokenizer.init_xgrammar()
            )
            if tokenizer_info is None:
                raise TokenizerNotSupportedError(
                    f"Tokenizer type {type(tokenizer).__name__} "
                    f"is not supported by XGrammar"
                )
        else:
            try:
                tokenizer_info = TokenizerInfo.from_huggingface(
                    tokenizer, vocab_size=vocab_size,
                    stop_token_ids=model_eos_token_ids
                )
                override_stop_tokens = None
            except Exception as e:
                raise TokenizerNotSupportedError(
                    f"Failed to create XGrammar TokenizerInfo: {e}"
                )

        self.grammar_compiler = GrammarCompiler(
            tokenizer_info=tokenizer_info
        )
        self.vocab_size = vocab_size
        self.override_stop_tokens = override_stop_tokens
        self.any_whitespace = any_whitespace
```

#### Frontend Language -- IR Primitives

This implements the SGLang DSL concept from Core Concepts. The intermediate representation defines primitives like `SglGen` (generation), `SglSelect` (constrained choices), and `SglFork` (parallel branching) that capture program structure for runtime optimization.

```python
# source: python/sglang/lang/ir.py:1-50
# github: sgl-project/sglang
# tag: v0.5.9
class SglExpr:
    """Base class for SGLang expression nodes."""
    def __add__(self, other):
        return SglExprList([self, other])

class SglGen(SglExpr):
    """Represents a call to generate text from the model.
    Accepts sampling params: max_new_tokens, temperature, top_p,
    and constrained generation: regex, json_schema."""
    def __init__(self, name, max_tokens, stop, **kwargs):
        self.name = name
        self.sampling_params = SglSamplingParams(
            max_new_tokens=max_tokens, stop=stop, **kwargs
        )

class SglSelect(SglExpr):
    """Handles selecting from a predefined list of choices."""
    def __init__(self, name, choices, temperature):
        self.name = name
        self.choices = choices
        self.temperature = temperature

class SglFork(SglExpr):
    """Creates multiple parallel execution branches."""
    def __init__(self, number, position_ids_offset=None):
        self.number = number
        self.position_ids_offset = position_ids_offset

class SglFunction:
    """Wraps user-defined functions into executable programs.
    Supports run(), run_batch(), and trace() execution modes."""
    def __init__(self, func):
        self.func = func
```

#### Speculative Decoding -- EAGLE Worker

This implements the speculative decoding concept. The `EAGLEWorker` manages the draft-verify cycle: it generates candidate tokens with a lightweight draft model, then verifies them against the target model in a single pass.

```python
# source: python/sglang/srt/speculative/eagle_worker.py:40-90
# github: sgl-project/sglang
# tag: v0.5.9
class EAGLEWorker(TpModelWorker):
    """Speculative decoding worker using the EAGLE algorithm.
    
    Draft Phase: generates candidate token tree using a smaller model
    that shares embeddings and language head with the target.
    
    Verify Phase: target model processes all candidates in one pass,
    accepting tokens that match the target distribution.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Draft model shares embeddings with target
        # Separate KV cache pools for draft predictions
        # CUDA graph capture for repeated draft patterns

    def draft(self, batch):
        """Generate candidate tokens via top-k sampling.
        Builds a tree of predictions across multiple steps."""
        # Token selection via top-k
        # Cache location allocation for speculative paths
        # Hidden state propagation across draft steps

    def verify(self, batch):
        """Validate drafts against target model logits.
        Accept matching tokens, reject at first mismatch."""
        # Batch-level verification against target logits
        # Grammar-constrained vocab mask generation
        # Logprob calculation for accepted tokens
```

#### Attention Backend -- FlashInfer Integration

This implements the attention backend component described in Architecture. The `FlashInferAttnBackend` manages FlashInfer kernel dispatch, handling different attention patterns (prefill vs decode, standard vs sliding window) and hardware-specific optimizations.

```python
# source: python/sglang/srt/layers/attention/flashinfer_backend.py:30-75
# github: sgl-project/sglang
# tag: v0.5.9
class FlashInferAttnBackend(AttentionBackend):
    """Flashinfer attention kernels."""

    def __init__(
        self,
        model_runner: ModelRunner,
        skip_prefill: bool = False,
        kv_indptr_buf: Optional[torch.Tensor] = None,
        kv_last_page_len_buf: Optional[torch.Tensor] = None,
        init_new_workspace: bool = False,
    ):
        super().__init__()
        self.prefill_backend = "fa2"
        self.decode_backend = "fa2"

        self.decode_use_tensor_cores = should_use_tensor_core(
            kv_cache_dtype=model_runner.kv_cache_dtype,
            num_attention_heads=(
                model_runner.model_config.num_attention_heads
                // get_attention_tp_size()
            ),
            num_kv_heads=model_runner.model_config.get_num_kv_heads(
                get_attention_tp_size()
            ),
        )
        self.max_context_len = model_runner.model_config.context_len
        self.skip_prefill = skip_prefill
        self.is_multimodal = model_runner.model_config.is_multimodal
        self.page_size = model_runner.page_size
```

### Deployment Considerations

**GPU Memory Sizing.** As a rule of thumb, allocate 2x the model size in GPU memory for serving (model weights + KV cache). For example, Llama-3.1-70B in FP16 requires ~140GB, so plan for 2-4 A100 80GB GPUs with `--tp-size 2` or `--tp-size 4`.

**Monitoring.** SGLang exposes Prometheus metrics when launched with `--enable-metrics`. Key metrics to watch: `sglang_num_running_requests` (batch size), `sglang_cache_hit_rate` (RadixAttention effectiveness), `sglang_token_throughput` (tokens/sec), and `sglang_time_to_first_token_seconds` (TTFT distribution).

**Quantization.** For memory-constrained deployments, use FP8 quantization (`--quantization fp8`) which halves memory usage with minimal quality loss on most models. INT4/AWQ/GPTQ provide further compression but with more noticeable quality trade-offs.

**Scaling Out.** For multi-GPU serving beyond tensor parallelism, use data parallelism with `--dp-size N` which launches N independent scheduler instances behind a load balancer. For latency-sensitive workloads, consider prefill/decode disaggregation which runs prefill and decode on separate GPU pools.

**Model Updates.** SGLang supports online weight updates without restarting the server, enabling seamless model version upgrades and LoRA adapter hot-swapping in production.
