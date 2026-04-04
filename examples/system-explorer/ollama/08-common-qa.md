## Common Q&A
<!-- level: all -->
<!-- references:
- [Ollama FAQ and Documentation](https://docs.ollama.com/) | official-docs
- [Ollama GitHub Issues](https://github.com/ollama/ollama/issues) | github
- [Ollama Community Discussions](https://github.com/ollama/ollama/discussions) | community
-->

### Q: How much RAM/VRAM do I actually need to run a model?

A Q4_K_M quantized model needs roughly 0.6 GB per billion parameters for weights alone. So a 7B model needs ~4.5 GB, a 13B model needs ~8 GB, and a 70B model needs ~40 GB. Add 10-20% for KV cache at default context lengths (2048-4096 tokens), more for extended contexts. On Apple Silicon, Ollama uses unified memory, so your total system RAM is your VRAM budget. On discrete GPUs, if the model does not fit entirely in VRAM, Ollama automatically splits layers between GPU and CPU -- usable but significantly slower. For a practical minimum: 8 GB RAM lets you run 7B models, 16 GB handles 13B, and 32 GB can run some 30B models.

### Q: What happens if a model is too large for my GPU memory?

Ollama gracefully handles this. The Scheduler's layer assignment uses binary search to find the optimal split between GPU and CPU. Layers that fit in VRAM run on the GPU; the rest run on CPU with system RAM. This "partial offload" is slower than full GPU (typically 2-5x slower for the CPU-bound layers) but faster than pure CPU. You can monitor the split with `ollama ps`, which shows the GPU/CPU percentage for each loaded model. To force full CPU mode, set `OLLAMA_NUM_GPU=0`.

### Q: Why is the first request to a model so slow, but subsequent requests are fast?

The first request triggers model loading: reading the GGUF file from disk, allocating GPU memory, and loading weights into VRAM. This cold start takes 2-10 seconds for 7B models and up to 60 seconds for 70B models. Once loaded, the model stays in memory for the `keep_alive` duration (default: 5 minutes). Subsequent requests skip the loading step and go directly to inference, with first-token latency in the low hundreds of milliseconds. Set `OLLAMA_KEEP_ALIVE=-1` to keep models permanently loaded and eliminate cold starts entirely.

### Q: Can I run multiple models simultaneously?

Yes, Ollama's Scheduler supports multiple loaded models. By default, `OLLAMA_MAX_LOADED_MODELS=0` means Ollama auto-detects how many models fit based on available memory. It loads models on demand and evicts the least-recently-used model when memory is needed. You can request from different models concurrently -- each gets its own Runner subprocess. The Scheduler also supports parallel requests to the same model via `OLLAMA_NUM_PARALLEL`. Watch out for memory pressure: two 7B models need ~9 GB, which is tight on a 16 GB machine.

### Q: How do I use Ollama as a drop-in replacement for the OpenAI API?

Set the base URL to `http://localhost:11434/v1` and use any API key (Ollama ignores it). With the Python OpenAI SDK: `client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")`. The `/v1/chat/completions`, `/v1/completions`, and `/v1/embeddings` endpoints implement the OpenAI specification. Most features work -- streaming, tool calling, structured outputs, system messages. Some advanced features (function calling with strict mode, logprobs on all tokens) may have partial support depending on the model.

### Q: How does Ollama compare to running llama.cpp directly?

Ollama wraps llama.cpp and adds model management (pulling, storing, versioning), automatic GPU detection, a persistent server, model scheduling (load/unload/eviction), and the OpenAI-compatible API. The trade-off is ~5-15% performance overhead and less control over low-level settings. Use raw llama.cpp if you need maximum tokens/second, custom CUDA kernels, speculative decoding, or want to avoid the abstraction layer. Use Ollama if you value convenience, want multiple models managed automatically, or need an API server for application integration.

### Q: What is the diagnostic approach when generation is unexpectedly slow?

Start with `ollama ps` to check how many layers are on GPU vs CPU -- partial offload is the most common cause of slowness. Then check `OLLAMA_NUM_PARALLEL`: too many parallel requests on a single model causes contention. Verify no other process is consuming GPU memory (check `nvidia-smi` on NVIDIA or Activity Monitor on macOS). If the model fits in VRAM but is still slow, try enabling flash attention (`OLLAMA_FLASH_ATTENTION=1`) and reducing context length (`num_ctx`). On Linux, ensure you are using the proprietary NVIDIA driver, not nouveau. For Apple Silicon, check that Ollama is using Metal (it should automatically, but Rosetta translation mode disables it).

### Q: How do I create a custom model with a specific persona or behavior?

Create a Modelfile with your customizations and build it with `ollama create`. Example: create a file named `Modelfile` containing `FROM llama3.2`, `PARAMETER temperature 0.3`, `SYSTEM "You are a senior Python developer. Always include type hints. Explain your reasoning."`, then run `ollama create python-expert -f Modelfile`. The resulting model appears in `ollama list` and can be run with `ollama run python-expert`. You can also set templates, adapter weights (LoRA), and any inference parameter. Custom models share the base model's weights, so they consume minimal additional disk space.
