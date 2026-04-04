## Architecture
<!-- level: intermediate -->
<!-- references:
- [Ollama GitHub Repository](https://github.com/ollama/ollama) | github
- [Ollama API Reference](https://docs.ollama.com/api/) | official-docs
- [llama.cpp Project](https://github.com/ggerganov/llama.cpp) | github
-->

### High-Level Design

Ollama follows a client-server architecture with a process-per-model isolation pattern. The system has four main layers:

```
  CLI / HTTP Client
        |
  [REST API Server]  (Gin HTTP router + OpenAI compat layer)
        |
  [Scheduler]         (model lifecycle, memory management, eviction)
        |
  [Runner Process]    (llama.cpp / MLX inference subprocess per model)
        |
  [GPU / CPU]         (CUDA, ROCm, Metal, or CPU fallback)
```

The CLI and API clients send requests to a persistent HTTP server. The server delegates model lifecycle to a Scheduler that tracks loaded models and GPU memory. When inference is needed, the Scheduler ensures a Runner subprocess is alive and routes the request to it. Runners are isolated processes that communicate with the server over local HTTP, so a crash in one model's inference does not bring down the server.

### Key Components

**REST API Server (server/routes.go)** -- Routes HTTP requests to handlers. Exists because Ollama needs a stable, language-agnostic interface for the many client libraries and integrations that depend on it. Built on the Gin framework, it handles CORS, host validation, and provides both Ollama-native endpoints (`/api/chat`, `/api/generate`) and OpenAI-compatible endpoints (`/v1/chat/completions`). The dual API surface means developers can switch between Ollama and OpenAI without changing their code.

**Scheduler (server/sched.go)** -- Manages the lifecycle of loaded models. Exists because GPU memory is scarce and expensive -- you cannot have every model loaded simultaneously on consumer hardware. The Scheduler maintains a map of loaded runners, handles concurrent request queuing, implements memory-aware eviction (unloading the least-recently-used model when GPU memory is needed), and manages keep-alive timers. Without it, users would have to manually load and unload models.

**Runner / LlamaServer (llm/server.go)** -- The inference execution layer. Exists because LLM inference requires tight control over GPU memory allocation, context windowing, and token sampling. Each model runs in its own subprocess, communicating over a local HTTP port. This process isolation means a segfault in the C++ inference code does not crash the Go server. The Runner abstracts two backends: legacy llama.cpp and the newer Ollama engine with MLX support.

**Model Store (blob storage)** -- Content-addressable storage for model files. Exists because models can be multi-gigabyte files that share layers (like Docker images share base layers). Models are stored as manifests pointing to blob digests, so pulling a variant of a model you already have only downloads the changed layers. This design mirrors container registries and saves disk space and bandwidth.

**GPU Discovery (discover/)** -- Hardware detection subsystem. Exists because Ollama must automatically detect and utilize whatever GPU hardware is available without manual configuration. It probes for NVIDIA CUDA, AMD ROCm, Apple Metal, and NVIDIA Jetson platforms, reporting available VRAM and compute capability to the Scheduler.

**Model Converter (convert/)** -- Transforms models from training formats (SafeTensors, PyTorch) to GGUF. Exists because the open-source model ecosystem publishes models in various formats, but the inference engine requires GGUF. The converter supports 25+ model architectures (Llama, Mistral, Gemma, Qwen, etc.) and handles tensor name remapping, vocabulary processing, and quantization.

### Data Flow

A typical chat request flows through the system in these steps:

1. **Client sends request** -- `POST /api/chat` with model name and messages
2. **Server parses request** -- Validates model reference, checks if model exists locally
3. **Scheduler checks cache** -- Looks up model in loaded runners map by model key
4. **If not loaded: pull + load** -- Downloads model from registry if missing, selects GPUs via discovery, spawns Runner subprocess, waits for health check
5. **If loaded: reuse** -- Increments reference count on existing runner, resets expiration timer
6. **Runner executes inference** -- Tokenizes input, runs forward passes through the model, samples tokens
7. **Stream response** -- Tokens are streamed back via Server-Sent Events to the API server, then to the client
8. **Cleanup** -- Reference count decremented; if model goes idle, expiration timer starts

### Design Decisions

**Process-per-model isolation over in-process loading.** Ollama runs each model in a separate OS process rather than loading models into the server's memory space. This costs some IPC overhead but means a crash in the C/C++ inference code (common with new model architectures) does not take down the API server. It also enables clean memory reclamation -- killing a process guarantees its GPU memory is freed.

**Content-addressable blob storage over flat files.** Models are stored as digests referencing blobs, with manifests pointing to layers. This mirrors Docker's storage model and enables layer sharing between model variants. A 7B base model and its fine-tuned variant share the base weights, saving gigabytes of disk space.

**OpenAI API compatibility as a first-class concern.** By providing `/v1/chat/completions`, Ollama can be a drop-in replacement for OpenAI in any application that uses the OpenAI SDK. This was a deliberate choice to lower the barrier for developers migrating from cloud APIs to local inference.

**Automatic GPU memory management over manual configuration.** The Scheduler proactively tracks VRAM usage and evicts models when needed, rather than requiring users to specify memory limits. This makes Ollama "just work" on consumer hardware, at the cost of some predictability for advanced users who want fine-grained control.
