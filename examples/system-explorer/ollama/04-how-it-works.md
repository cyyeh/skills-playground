## How It Works
<!-- level: intermediate -->
<!-- references:
- [llama.cpp GGUF Specification](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md) | github
- [Ollama Modelfile Reference](https://docs.ollama.com/modelfile) | official-docs
- [Ollama API Reference](https://docs.ollama.com/api/) | official-docs
-->

### Model Pulling and Storage

When you run `ollama pull llama3.2`, Ollama contacts its model registry at `registry.ollama.ai` and downloads a manifest -- a JSON document listing the model's layers with their digests and media types. Each layer is a content-addressed blob (identified by SHA256 hash) stored in `~/.ollama/models/blobs/`. The layer types include:

- **Model weights** (`application/vnd.ollama.image.model`) -- The GGUF file containing quantized weights
- **Chat template** (`application/vnd.ollama.image.template`) -- Go template defining the prompt format
- **Parameters** (`application/vnd.ollama.image.params`) -- Default inference parameters (temperature, top_p, etc.)
- **System prompt** (`application/vnd.ollama.image.system`) -- Default system message
- **License** (`application/vnd.ollama.image.license`) -- Model license text
- **Adapters** (`application/vnd.ollama.image.adapter`) -- LoRA adapter weights

Because blobs are content-addressed, pulling a fine-tuned variant of a model you already have skips downloading shared layers. The manifest for `llama3.2:3b` and `llama3.2:3b-instruct` might share the same base weights blob, differing only in the template and parameters layers.

### Model Loading and GPU Allocation

When a model needs to be loaded, the Scheduler orchestrates a multi-step process:

1. **Hardware discovery** -- The `discover` package probes the system for available GPUs, reporting device type (CUDA, ROCm, Metal), total VRAM, free VRAM, and compute capability
2. **Memory estimation** -- Based on the GGUF file's metadata (layer count, tensor sizes, context length), the system estimates how much VRAM the model will consume
3. **Layer assignment** -- The `assignLayers` function uses binary search to determine the optimal distribution of model layers across available GPUs. Layers that do not fit in VRAM are assigned to CPU RAM
4. **Eviction if needed** -- If not enough memory is available, the Scheduler evicts idle models (those with zero active requests and the shortest session duration first)
5. **Runner spawn** -- A subprocess is started with environment variables for the selected GPU libraries (CUDA paths, ROCm paths, etc.), assigned an ephemeral TCP port, and begins loading model weights
6. **Health polling** -- The server polls the runner's `/health` endpoint until it reports ready, with stall detection that aborts if loading stops making progress

The three-phase load protocol (Fit, Alloc, Commit) for the newer Ollama engine allows the system to first check whether a model fits, then allocate GPU memory, then commit by loading actual weights -- enabling graceful fallback to CPU if GPU memory is insufficient.

### Inference Pipeline

Once a model is loaded, each inference request follows this pipeline:

1. **Template rendering** -- The chat messages are formatted using the model's Go template (from the Modelfile or GGUF metadata). This converts the structured `[{role, content}]` format into the raw prompt format the model expects (e.g., `<|im_start|>user\nHello<|im_end|>`)
2. **Tokenization** -- The rendered prompt is split into token IDs using the model's vocabulary (BPE, SentencePiece, or similar)
3. **Context management** -- If the token count exceeds the model's context window, Ollama can truncate or shift the context. The `num_keep` parameter preserves the system prompt while sliding the conversation window
4. **Forward pass** -- Tokens are fed through the model's transformer layers, computing attention and feed-forward operations on GPU/CPU
5. **Sampling** -- The output logits are converted to token probabilities, with sampling controlled by `temperature`, `top_k`, `top_p`, `min_p`, and repetition penalty parameters
6. **Streaming** -- Each generated token is immediately sent back to the API server via the local HTTP connection, which streams it to the client as a Server-Sent Event (SSE)

### Scheduler and Memory Management

The Scheduler is the most operationally critical component. It runs two goroutines in parallel:

**processPending** -- Dequeues model load requests, checks if an existing runner can serve the request (same model, compatible options, healthy process), and if not, triggers a new load. When the system hits its `MaxRunners` limit, it calls `findRunnerToUnload` to evict the least valuable runner.

**processCompleted** -- Tracks when requests finish (decrementing reference counts), sets expiration timers on idle models, and handles the cleanup when a timer fires. When a model is unloaded from a discrete GPU, `waitForVRAMRecovery` polls the GPU driver until 75% of the model's VRAM is confirmed freed -- this prevents the scheduler from trying to load a new model before the GPU driver has actually reclaimed the memory.

The eviction strategy prioritizes unloading models that have the shortest configured session duration and are currently idle (zero active requests). If all models are active, it falls back to evicting the one with the shortest session duration regardless.

### Model Conversion Pipeline

When users create models from non-GGUF formats (via `ollama create` with SafeTensors or PyTorch files), the convert package handles the transformation:

1. **Architecture detection** -- Reads `config.json` from the model directory to identify the architecture (LlamaForCausalLM, GemmaForCausalLM, etc.)
2. **Tensor name remapping** -- Each architecture has specific tensor naming conventions; the converter maps them to GGUF's standardized names
3. **Tokenizer processing** -- Extracts vocabulary, merge rules, and special tokens from the tokenizer files
4. **Weight conversion** -- Reads tensors from SafeTensors/PyTorch format, applies any necessary transformations (shape reversal, type casting), and writes them in GGUF format
5. **Optional quantization** -- If requested, quantizes the full-precision weights to a specified level (Q4_K_M, Q5_K_M, Q8_0, etc.)

### Performance Characteristics

**Token generation speed** depends heavily on hardware and model size. On an M3 MacBook Pro with 36GB RAM, a 7B Q4_K_M model typically generates 30-50 tokens/second. A 70B model on the same hardware drops to 5-10 tokens/second due to memory bandwidth limitations. NVIDIA GPUs with ample VRAM can be significantly faster -- an RTX 4090 can push 80+ tokens/second on 7B models.

**Cold start time** (loading a model from disk) ranges from 2-10 seconds for 7B models to 30-60 seconds for 70B models, depending on disk speed and GPU memory bandwidth. Once loaded, subsequent requests benefit from the keep-alive cache and start in milliseconds.

**Context window overhead** scales quadratically with context length for models without efficient attention. Doubling the context window roughly quadruples the memory needed for the KV cache. Ollama supports flash attention and KV cache quantization to mitigate this on supported hardware.
