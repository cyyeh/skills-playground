## Implementation Details
<!-- level: advanced -->
<!-- references:
- [Quick Start Guide](https://nvidia.github.io/TensorRT-LLM/quick-start-guide.html) | official-docs
- [trtllm-build Command](https://nvidia.github.io/TensorRT-LLM/latest/commands/trtllm-build.html) | official-docs
- [Performance Tuning Guide](https://nvidia.github.io/TensorRT-LLM/performance/performance-tuning-guide/index.html) | official-docs
- [Build-Time Flags](https://nvidia.github.io/TensorRT-LLM/performance/performance-tuning-guide/useful-build-time-flags.html) | official-docs
- [TensorRT-LLM GitHub](https://github.com/NVIDIA/TensorRT-LLM) | github
-->

### Getting Started

**Docker (recommended):**
```bash
docker run --rm -it --ipc host --gpus all --ulimit memlock=-1 \
  --ulimit stack=67108864 -p 8000:8000 \
  nvcr.io/nvidia/tensorrt-llm/release:1.3.0rc10
```

**Pip install:**
```bash
pip install tensorrt-llm
# Requires: Python 3.10/3.12, CUDA 13.1.1+, PyTorch 2.10.0+
```

**First inference — OpenAI-compatible server:**
```bash
trtllm-serve "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Test with curl:
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 32,
    "temperature": 0
  }'
```

**First inference — Python API:**
```python
from tensorrt_llm import LLM, SamplingParams

llm = LLM(model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
prompts = ["Hello, my name is", "The capital of France is"]
sampling_params = SamplingParams(temperature=0.8, top_p=0.95)

for output in llm.generate(prompts, sampling_params):
    print(f"Prompt: {output.prompt!r}")
    print(f"Generated: {output.outputs[0].text!r}")
```

**Pre-quantized models (skip compilation):**
```bash
trtllm-serve "nvidia/Qwen3-8B-FP8"
```

### Configuration Essentials

| Parameter | Default | What It Controls | When to Change |
|-----------|---------|-----------------|----------------|
| `--multiple_profiles` | off | Creates multiple TensorRT optimization profiles for different batch sizes | **Always enable** — only helps, slight build time increase |
| `--use_paged_context_fmha` | off | Chunks context (prefill) across iterations | Enable for long input sequences (>2K tokens) |
| `--gemm_plugin auto` | auto | Uses cuBLASLt and custom kernels for matrix multiplication | Enable for FP16/BF16; disable for FP8 (TRT native is faster) |
| `--reduce_fusion enable` | off | Fuses ResidualAdd+LayerNorm into AllReduce kernel | Enable for multi-GPU LLaMA/Mistral/Mixtral |
| `max_batch_size` | 256 | Maximum concurrent requests | Increase to 2048 for throughput-focused in-flight batching |
| `max_num_tokens` | 8192 | Token budget per iteration | Increase for high-throughput; decrease for low-latency |
| `enable_chunked_context` | off | Splits prefill into smaller chunks | Enable when mixing long and short requests |
| KV cache memory fraction | 0.9 | Fraction of free GPU memory allocated to KV cache | Lower if running other processes on the same GPU |
| `tokens_per_block` | 64 | KV cache block granularity | Smaller blocks (32) for variable-length; larger (128) for long contexts |
| `kv_cache_type` | fp16 | KV cache precision | Use `int8` or `fp8` to fit 2-4x more concurrent sequences |

Enabling all build-time optimization flags together yields ~30% throughput improvement and ~54% inter-token latency reduction on Llama 3.3 70B / 4× H100.

### Code Patterns

**Streaming generation:**
```python
from tensorrt_llm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-3.1-8B-Instruct")
sp = SamplingParams(temperature=0.7, max_tokens=256)

# Async streaming
async for output in llm.generate_async("Explain transformers", sp, streaming=True):
    print(output.outputs[0].text, end="", flush=True)
```

**Multi-GPU inference with tensor parallelism:**
```python
from tensorrt_llm import LLM, SamplingParams

# Automatically shards across 4 GPUs
llm = LLM(model="meta-llama/Llama-3.1-70B-Instruct",
           tensor_parallel_size=4)

output = llm.generate("What is TensorRT?",
                       SamplingParams(max_tokens=100))
print(output.outputs[0].text)
```

**FP8 quantization:**
```python
from tensorrt_llm import LLM, SamplingParams
from tensorrt_llm.llmapi import QuantConfig, QuantAlgo

llm = LLM(model="meta-llama/Llama-3.1-8B",
           quant_config=QuantConfig(quant_algo=QuantAlgo.FP8))

output = llm.generate("Hello world", SamplingParams(max_tokens=50))
```

**LoRA adapter loading:**
```python
from tensorrt_llm import LLM, SamplingParams
from tensorrt_llm.llmapi import LoRARequest

llm = LLM(model="meta-llama/Llama-3.1-8B-Instruct")
lora = LoRARequest(lora_name="my-adapter", lora_path="/path/to/adapter")

output = llm.generate("Summarize:", SamplingParams(max_tokens=100),
                       lora_request=lora)
```

### Source Code Walkthrough

#### Engine / Builder — Implementation

The Builder wraps TensorRT's native builder and handles the full compilation pipeline. This is the core of the "model-to-engine" transformation described in Core Concepts. The `build()` function is the top-level entry point that takes a model graph, applies quantization and plugin optimizations, then delegates to TensorRT's compiler.

```python
# source: tensorrt_llm/builder.py
# github: NVIDIA/TensorRT-LLM
# tag: v1.2.0
class Builder():
    """Wraps TensorRT's trt.Builder to build TensorRT-LLM engines."""

    def __init__(self):
        super().__init__()
        self._trt_builder = trt.Builder(logger.trt_logger)

    def create_network(self):
        network = self._trt_builder.create_network()
        return network

    def create_builder_config(self, precision, timing_cache, ...):
        config = self._trt_builder.create_builder_config()
        # Set precision flags, workspace size, plugin configs
        return config

    @_is_building
    def build_engine(self, network, builder_config, managed_weights):
        """Compile the network into a serialized TensorRT engine."""
        self._add_optimization_profile(network, builder_config)
        # TensorRT compiles: kernel selection, layer fusion, auto-tuning
        return self._trt_builder.build_serialized_network(
            network, builder_config)
```

The `Engine` class wraps the compiled binary with its configuration for serialization:

```python
# source: tensorrt_llm/builder.py
# github: NVIDIA/TensorRT-LLM
# tag: v1.2.0
class Engine:
    """Holds a serialized TRT engine + config + managed weights."""

    def __init__(self, config: EngineConfig, engine: trt.IHostMemory,
                 managed_weights=None):
        self.config = config
        self.engine = engine
        self.managed_weights = managed_weights

    def save(self, engine_dir: str):
        """Serialize engine binary and config to disk."""
        os.makedirs(engine_dir, exist_ok=True)
        with open(os.path.join(engine_dir, 'config.json'), 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)
        with open(os.path.join(engine_dir, f'rank{rank}.engine'), 'wb') as f:
            f.write(self.engine)

    @classmethod
    def from_dir(cls, engine_dir: str):
        """Load a previously compiled engine from disk."""
        config = EngineConfig.from_json_file(
            os.path.join(engine_dir, 'config.json'))
        with open(os.path.join(engine_dir, f'rank{rank}.engine'), 'rb') as f:
            engine = f.read()
        return cls(config, engine)
```

#### LLM API — Implementation

The `LLM` class is the high-level entry point described in Core Concepts. It inherits from `_TorchLLM` (PyTorch backend) which inherits from `BaseLLM`. The `generate()` method handles batching, async submission, and result collection.

```python
# source: tensorrt_llm/llmapi/llm.py
# github: NVIDIA/TensorRT-LLM
# tag: v1.2.0
class BaseLLM:
    """Abstract base handling tokenizer loading and generate dispatch."""

    def __init__(self, model, tokenizer, tokenizer_mode, skip_tokenizer_init,
                 trust_remote_code, tensor_parallel_size, dtype, revision,
                 tokenizer_revision, **kwargs):
        self._executor_cls = kwargs.pop("executor_cls", GenerationExecutor)
        self._orchestrator_type = kwargs.get("orchestrator_type", None)
        # ... tokenizer loading, model resolution

    def generate(self, inputs, sampling_params, use_tqdm=True, **kwargs):
        """Synchronous batch generation."""
        unbatched = not isinstance(inputs, list)
        if unbatched:
            inputs = [inputs]
        futures = []
        for i, prompt in enumerate(inputs):
            future = self.generate_async(prompt, sampling_params=sp, **kwargs)
            futures.append(future)
        for future in futures:
            future.result()  # Block until complete
        return [RequestOutput.from_future(f) for f in futures]
```

```python
# source: tensorrt_llm/llmapi/llm.py
# github: NVIDIA/TensorRT-LLM
# tag: v1.2.0
class LLM(_TorchLLM):
    """Main public class. Uses PyTorch backend by default (v1.0+)."""
    pass

class _TorchLLM(BaseLLM):
    """PyTorch-native backend using PyExecutor."""

    def _build_model(self):
        # Resolves model from HuggingFace, applies quantization,
        # initializes PyExecutor with the model
        ...
```

#### KV Cache — Implementation

The C++ `KVCacheManager` implements the paged KV cache concept. Its constructor reveals the complexity of managing block pools across layers, attention windows, and quantization modes.

```cpp
// source: cpp/include/tensorrt_llm/batch_manager/kvCacheManager.h
// github: NVIDIA/TensorRT-LLM
// tag: v1.2.0
class KVCacheManager : public BaseKVCacheManager {
public:
    KVCacheManager(
        std::vector<SizeType32> const& numKvHeadsPerLayer,
        SizeType32 sizePerHead, SizeType32 tokensPerBlock,
        BlocksPerWindow const& blocksPerWindow,
        SizeType32 maxNumSequences, SizeType32 maxBeamWidth,
        std::vector<SizeType32> const& maxAttentionWindowVec,
        nvinfer1::DataType dtype, SizeType32 sinkTokenLength,
        CudaStreamPtr stream, SizeType32 maxSequenceLength,
        bool enableBlockReuse = false, bool onboardBlocks = true,
        CacheType cacheType = CacheType::kSELF);

    // Core lifecycle methods
    void addSequence(RequestId requestId, SizeType32 inputLength,
                     SizeType32 beamWidth);
    void addToken(RequestId requestId);
    void removeSequence(RequestId requestId);

    // Capacity queries
    [[nodiscard]] SizeType32 getNumFreeBlocks() const;
    [[nodiscard]] SizeType32 getUsedNumBlocks() const;

    // Paged attention offset table for GPU kernels
    void getBlockOffsetsOfBatch(ITensor& output) const;

    // Prefix caching
    void storeContextBlocks(RequestId requestId);
    BlockPtr findNewContextBlock(TokenRange const& tokens);

    // Speculative decoding support
    void rewindKVCache(RequestId requestId,
                       std::vector<SizeType32> const& rewindLengths);
};
```

The Python-side `BlocksManager` shows the block pool's physical layout:

```python
# source: tensorrt_llm/runtime/kv_cache_manager.py
# github: NVIDIA/TensorRT-LLM
# tag: v1.2.0
class BlocksManager:
    """Manages a pool of KV cache blocks."""

    def __init__(self, num_blocks, num_layers, block_size, num_kv_heads,
                 head_size, dtype):
        # Pool shape: [num_blocks, num_layers, 2, num_kv_heads, block_size, head_size]
        # The '2' dimension holds Key and Value separately
        self.pool = torch.zeros(
            num_blocks, num_layers, 2, num_kv_heads, block_size, head_size,
            dtype=dtype, device='cuda')
        self.free_blocks = list(range(num_blocks))

    def allocate(self):
        """Pop a free block from the pool."""
        if not self.free_blocks:
            raise RuntimeError("KV cache OOM: no free blocks")
        return self.free_blocks.pop()

    def free(self, block_id):
        """Return a block to the free pool."""
        self.free_blocks.append(block_id)
```

#### In-Flight Batching — Implementation

The scheduling pipeline implements the in-flight batching concept. The `PyMicroBatchScheduler` splits admitted requests into context (prefill) and generation batches — the core of continuous batching.

```python
# source: tensorrt_llm/_torch/pyexecutor/scheduler/scheduler.py
# github: NVIDIA/TensorRT-LLM
# tag: v1.2.0
class PyMicroBatchScheduler(MicroBatchScheduler):
    """Partitions active requests into context vs. generation batches."""

    def schedule(self, active_requests, inflight_request_ids):
        context_requests = []
        generation_requests = []
        batch_num_tokens = 0
        for req in active_requests:
            if req.request_id in inflight_request_ids:
                continue
            if req.state == RequestState.CONTEXT_INIT:
                # New request: needs prefill
                context_requests.append(req)
            elif req.state == RequestState.GENERATION_IN_PROGRESS:
                # Existing request: generating tokens
                generation_requests.append(req)
            batch_num_tokens += req.num_tokens
            if batch_num_tokens > self.max_num_tokens:
                break
        return ScheduledRequests(context_requests, generation_requests)
```

The capacity scheduler implements admission control with eviction policies:

```python
# source: tensorrt_llm/_torch/pyexecutor/scheduler/scheduler.py
# github: NVIDIA/TensorRT-LLM
# tag: v1.2.0
class GuaranteedNoEvictPolicy:
    """Only admits a request if guaranteed not to evict existing sequences."""

    def schedule(self, active_requests, kv_cache_manager):
        scheduled = []
        paused = []
        for req in active_requests:
            blocks_needed = self._estimate_blocks(req)
            if kv_cache_manager.getNumFreeBlocks() >= blocks_needed:
                scheduled.append(req)
            else:
                paused.append(req)
        return scheduled, paused
```

#### Quantization — Implementation

The `QuantAlgo` enum and `quantize()` dispatcher implement the quantization concept. The enum defines 25+ algorithms; the dispatcher replaces standard layers with quantized variants.

```python
# source: tensorrt_llm/quantization/mode.py
# github: NVIDIA/TensorRT-LLM
# tag: v1.2.0
class QuantAlgo(StrEnum):
    W8A16 = "W8A16"
    W4A16 = "W4A16"
    W4A16_AWQ = "W4A16_AWQ"
    W4A8_AWQ = "W4A8_AWQ"
    W4A16_GPTQ = "W4A16_GPTQ"
    FP8 = "FP8"
    FP8_PER_CHANNEL_PER_TOKEN = "FP8_PER_CHANNEL_PER_TOKEN"
    INT8 = "INT8"
    NVFP4 = "NVFP4"
    W4A8_MXFP4_FP8 = "W4A8_MXFP4_FP8"
    # ... 15+ more variants

class QuantMode(IntFlag):
    """Bitmask for quantization mode combinations."""
    INT4_WEIGHTS = auto()
    INT8_WEIGHTS = auto()
    ACTIVATIONS = auto()
    PER_CHANNEL = auto()
    PER_TOKEN = auto()
    PER_GROUP = auto()
    INT8_KV_CACHE = auto()
    FP8_KV_CACHE = auto()
    FP8_QDQ = auto()
    NVFP4 = auto()
```

The `FP8Linear` layer shows how quantized inference works at the layer level:

```python
# source: tensorrt_llm/quantization/layers.py
# github: NVIDIA/TensorRT-LLM
# tag: v1.2.0
class FP8Linear(Linear):
    """FP8 quantized linear layer with per-tensor scaling."""

    def __init__(self, in_features, out_features, bias=True, dtype=None,
                 tp_group=None, tp_size=1, gather_output=True):
        super().__init__(in_features, out_features, bias, dtype,
                         tp_group, tp_size, gather_output)
        self.activation_scaling_factor = Parameter(shape=(1,), dtype='float32')
        self.weights_scaling_factor = Parameter(shape=(1,), dtype='float32')

    def forward(self, x, lora_runtime_params=None):
        alpha = (self.weights_scaling_factor.raw_value *
                 self.activation_scaling_factor.raw_value)
        # Quantize input to FP8, multiply with quantized weights,
        # apply combined scaling factor for dequantization
        return quantized_matmul(x, self.weight, alpha, self.bias)
```

#### Plugins — Implementation

The GPT Attention plugin is the most complex plugin, handling paged KV cache, Flash Attention, RoPE, quantization, and speculative decoding in a single fused kernel. Its constructor signature reveals the breadth of LLM attention requirements:

```cpp
// source: cpp/tensorrt_llm/plugins/gptAttentionPlugin/gptAttentionPlugin.h
// github: NVIDIA/TensorRT-LLM
// tag: v1.2.0
class GPTAttentionPlugin : public GPTAttentionPluginCommon {
public:
    GPTAttentionPlugin(
        int layer_idx, int num_heads, int vision_start, int vision_length,
        int num_kv_heads, int num_kv_heads_origin, int head_size,
        int unidirectional, float q_scaling,
        float attn_logit_softcapping_scale,
        PositionEmbeddingType position_embedding_type,
        int rotary_embedding_dim, float rotary_embedding_base,
        RotaryScalingType rotary_embedding_scale_type,
        // ... 40+ parameters covering:
        // - RoPE variants (NTK, YaRN, dynamic)
        // - Tensor parallelism config
        // - FMHA type (flash, xqa)
        // - KV cache quantization mode (int8, fp8, fp4)
        // - Paged KV cache settings (tokens_per_block)
        // - Cross-attention flags
        // - Speculative decoding parameters
        // - Multi-Latent Attention (MLA) for DeepSeek
        // - Context parallelism settings
        bool paged_kv_cache, int tokens_per_block,
        nvinfer1::DataType kv_cache_quant_mode,
        bool enable_xqa, ContextFMHAType context_fmha_type);
};
```

The plugin registration API shows how custom kernels integrate with TensorRT:

```cpp
// source: cpp/include/tensorrt_llm/plugins/api/tllmPlugin.h
// github: NVIDIA/TensorRT-LLM
// tag: v1.2.0
namespace tensorrt_llm::plugins::api {
    constexpr char const* kDefaultNamespace = "tensorrt_llm";

    // Register all TRT-LLM plugins with the TensorRT runtime
    bool initTrtLlmPlugins();

    // Auto-discovery callback for TensorRT's plugin registry
    void setLoggerFinder();

    // Returns array of all registered plugin creators
    IPluginCreator* const* getPluginCreators();
}
```

#### Executor — Implementation

The C++ `Executor` API is the lowest-level runtime interface — the "air traffic controller" from Core Concepts:

```cpp
// source: cpp/include/tensorrt_llm/executor/executor.h
// github: NVIDIA/TensorRT-LLM
// tag: v1.2.0
class Executor {
public:
    Executor(std::filesystem::path const& modelPath,
             ModelType modelType,
             ExecutorConfig const& executorConfig);

    [[nodiscard]] IdType enqueueRequest(Request const& request);
    [[nodiscard]] std::vector<IdType> enqueueRequests(
        std::vector<Request> const& requests);

    [[nodiscard]] std::vector<Response> awaitResponses(
        std::optional<std::chrono::milliseconds> const& timeout = std::nullopt);

    void cancelRequest(IdType requestId);
    void shutdown();

    std::deque<IterationStats> getLatestIterationStats();
    [[nodiscard]] bool canEnqueueRequests() const;
};
```

The Python `PyExecutor` implements the main inference loop that ties scheduling, execution, and sampling together:

```python
# source: tensorrt_llm/_torch/pyexecutor/py_executor.py
# github: NVIDIA/TensorRT-LLM
# tag: v1.2.0
class PyExecutor:
    """PyTorch-path executor with its own scheduling loop."""

    def _executor_loop(self):
        torch.cuda.set_device(self.device_id)
        with self._profiler() as profile_step, self.hang_detector:
            while True:
                self.hang_detector.checkpoint()
                profile_step()

                # 1. Fetch new requests and schedule
                scheduled_batch, iter_stats = self._prepare_and_schedule_batch()
                self._handle_control_request()

                if scheduled_batch is None:
                    break

                # 2. Pause/terminate requests that can't fit
                self._terminate_requests(scheduled_batch.terminated_requests)
                self._pause_requests(scheduled_batch.paused_requests)

                # 3. Forward pass + sampling
                finished_requests = []
                can_queue, _ = self._can_queue(scheduled_batch)
                # ... model forward, token sampling, response dispatch
```

#### Model Definition — Implementation

Model definitions follow a consistent pattern across all 80+ architectures. Using LLaMA as the exemplar (it's the most commonly used), the `MODEL_MAP` registry maps HuggingFace architecture names to TRT-LLM classes:

```python
# source: tensorrt_llm/models/__init__.py
# github: NVIDIA/TensorRT-LLM
# tag: v1.2.0
MODEL_MAP = {
    'LlamaForCausalLM': LLaMAForCausalLM,
    'MistralForCausalLM': LLaMAForCausalLM,  # Mistral reuses LLaMA
    'MixtralForCausalLM': LLaMAForCausalLM,
    'Qwen2ForCausalLM': Qwen2ForCausalLM,
    'GPT2LMHeadModel': GPTForCausalLM,
    'FalconForCausalLM': FalconForCausalLM,
    'DeepseekV3ForCausalLM': DeepseekV3ForCausalLM,
    'GemmaForCausalLM': GemmaForCausalLM,
    # ... 80+ architecture mappings
}
```

The `LLaMAForCausalLM` class shows the standard model construction pattern:

```python
# source: tensorrt_llm/models/llama/model.py
# github: NVIDIA/TensorRT-LLM
# tag: v1.2.0
class LLaMAForCausalLM(DecoderModelForCausalLM):
    """Full causal LM: transformer stack + language model head."""

    def __init__(self, config: LLaMAConfig):
        transformer = LLaMAModel(config)
        vocab_size_padded = pad_vocab_size(
            config.vocab_size, config.mapping.tp_size)
        if config.mapping.is_last_pp_rank():
            lm_head = ColumnLinear(
                config.hidden_size, vocab_size_padded, bias=False,
                dtype=config.dtype, tp_group=config.mapping.tp_group,
                tp_size=config.mapping.tp_size, gather_output=True)
        else:
            lm_head = None
        self.quant_mode = config.quant_mode
        super().__init__(config, transformer, lm_head)
```

### Deployment Considerations

**Hardware requirements:**
- Minimum: NVIDIA GPU with compute capability 8.0+ (A100, H100, L40S, B200)
- Recommended: H100 80GB SXM or B200 for production workloads
- Multi-GPU: NVLink/NVSwitch required for efficient tensor parallelism

**Engine management:**
- Engines are compiled per GPU architecture — maintain separate builds for each GPU type in your fleet
- Cache compiled engines to avoid the ~28-minute cold start
- Use `trtllm-bench` to benchmark before deploying: validate throughput and latency targets

**Monitoring:**
- `IterationStats` from the Executor provides per-step metrics (batch size, queue depth, KV cache utilization)
- KV cache utilization is the primary resource bottleneck — monitor `getNumFreeBlocks()` / total blocks
- TTFT and inter-token latency should be tracked at p50/p95/p99

**Scaling patterns:**
- Vertical: Tensor parallelism across GPUs within a node (NVLink)
- Horizontal: Pipeline parallelism across nodes (InfiniBand/RoCE)
- Disaggregated: Separate prefill and decode GPU pools for mixed workloads

**Upgrade path:**
- Engine format changes between major versions — recompile engines after upgrading
- The PyTorch workflow (v1.0+) provides more stable model compatibility than the legacy TensorRT path
- Pin specific container versions in production (`nvcr.io/nvidia/tensorrt-llm/release:1.2.0`, not `latest`)
