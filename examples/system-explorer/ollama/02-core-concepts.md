## Core Concepts
<!-- level: beginner -->
<!-- references:
- [Ollama Modelfile Reference](https://docs.ollama.com/modelfile) | official-docs
- [GGUF Format Specification](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md) | github
- [Ollama API Reference](https://docs.ollama.com/api/) | official-docs
- [Ollama Model Library](https://ollama.com/library) | official-docs
-->

### Model Library

The **Model Library** is Ollama's curated registry of pre-built models -- like an app store for LLMs. When you type `ollama run llama3.2`, Ollama checks the library at [ollama.com/library](https://ollama.com/library), finds the right model variant for your hardware, and downloads it. Think of it as Docker Hub for language models: a central place where models are published with tags for different sizes and quantization levels (e.g., `llama3.2:3b-q4_K_M`). The library abstracts away the complexity of finding, downloading, and verifying model files.

### GGUF Format

**GGUF** (GPT-Generated Unified Format) is the binary file format that stores model weights and metadata. It is like a ZIP file specifically designed for neural networks -- it packages the model's weights, vocabulary, architecture parameters, and chat template into a single file that inference engines can memory-map directly. GGUF replaced the older GGML format and is designed for fast loading: the engine can start reading weights without parsing the entire file first. Every model Ollama runs is stored in GGUF format.

### Quantization

**Quantization** reduces the precision of model weights to use less memory and run faster -- like compressing a high-resolution photo to a smaller file while keeping it recognizable. A model trained with 16-bit floating point weights might be quantized to 4-bit integers (Q4_K_M), reducing memory usage by roughly 4x with modest quality loss. Ollama automatically selects appropriate quantization levels for your hardware. Common levels include Q4_K_M (good balance), Q5_K_M (higher quality), and Q8_0 (near-original quality but 2x the memory of Q4).

### Modelfile

A **Modelfile** is Ollama's recipe file for building custom models -- like a Dockerfile but for LLMs. It uses a simple declarative syntax with instructions like `FROM` (base model), `PARAMETER` (inference settings), `SYSTEM` (system prompt), and `TEMPLATE` (chat format). You write a Modelfile to customize a model's behavior, set its temperature, define a persona, or adapt a base model with a LoRA adapter. Example: `FROM llama3.2` followed by `SYSTEM "You are a helpful coding assistant"` creates a coding-focused variant.

### REST API

Ollama's **REST API** is the HTTP interface that applications use to talk to the inference server -- like a waiter taking orders and bringing back responses from the kitchen. The server listens on `localhost:11434` and provides endpoints for text generation (`/api/generate`), chat completion (`/api/chat`), embeddings (`/api/embed`), and model management (`/api/pull`, `/api/tags`). It also includes an [OpenAI-compatible endpoint](https://docs.ollama.com/api/) at `/v1/chat/completions`, making it a drop-in replacement for OpenAI's API in existing applications.

### Scheduler

The **Scheduler** is Ollama's internal brain for managing which models are loaded in memory -- like an air traffic controller deciding which planes get to land and take off. Since models can consume gigabytes of GPU memory, the scheduler tracks loaded models, handles concurrent requests, manages memory pressure, and decides when to evict idle models to make room for new ones. It implements a keep-alive mechanism: models stay loaded for a configurable duration after the last request, avoiding expensive reload cycles for frequently used models.

### Runner

A **Runner** is the inference subprocess that actually executes model computations -- like the engine in a car that does the real work while the dashboard (API) provides the interface. Ollama spawns a separate process for each loaded model, communicating with it over a local HTTP connection. The runner handles tokenization, context management, attention computation, and token sampling. Ollama currently supports two runner backends: a legacy llama.cpp-based runner and a newer native Ollama engine built on MLX for Apple Silicon.

### How They Fit Together

When you run `ollama run llama3.2`, the CLI sends a chat request to the REST API server. The server asks the Scheduler whether the model is already loaded. If not, the Scheduler checks the local blob store for the GGUF model file (downloading from the Model Library if needed), selects GPUs with enough memory, and spawns a Runner subprocess. The Runner loads the quantized weights from the GGUF file, warms up, and starts accepting inference requests. Meanwhile, the Scheduler tracks the Runner's memory usage and sets an expiration timer -- if no requests arrive within the keep-alive window, the Runner is stopped and its memory freed for other models. The Modelfile, if used, customizes the model's parameters and system prompt before inference begins.
