## Core Concepts
<!-- level: beginner -->
<!-- references:
- [Core Concepts - Architecture](https://nvidia.github.io/TensorRT-LLM/architecture/core-concepts.html) | official-docs
- [GPT Attention](https://nvidia.github.io/TensorRT-LLM/advanced/gpt-attention.html) | official-docs
- [Quantization in TRT-LLM](https://nvidia.github.io/TensorRT-LLM/blogs/quantization-in-TRT-LLM.html) | blog
-->

### Engine

A **TensorRT Engine** is the compiled, optimized binary that runs your model on the GPU — like a compiled C program versus an interpreted Python script. The compilation step analyzes every operation in your model, fuses layers together, selects the fastest CUDA kernels for your specific GPU, and bakes the weights into an optimized binary. The trade-off: engines are GPU-specific (an H100 engine won't run on an A100) and take time to compile (~28 minutes for a 70B model), but once built, they deliver maximum throughput.

### Builder

The **Builder** is the compiler that transforms a model definition into an Engine — like `gcc` for neural networks. It takes your model architecture plus optimization settings (quantization level, tensor parallelism degree, max sequence length) and produces the optimized binary. You interact with it through either the [Python API](https://nvidia.github.io/TensorRT-LLM/architecture/core-concepts.html) (`tensorrt_llm.Builder`) or the `trtllm-build` CLI command.

### LLM API

The **LLM API** is the high-level Python interface — like HuggingFace's `pipeline()` but with TensorRT optimization under the hood. You initialize it with a model name, and it handles downloading, compilation, and inference in one call. It's the recommended entry point for most users: `LLM("meta-llama/Llama-3-8B")` gets you from zero to optimized inference.

### KV Cache (Paged)

The **KV Cache** stores previously computed Key and Value tensors during autoregressive generation — like a notepad where the model writes down what it's already "read" so it doesn't re-read the entire prompt for each new token. TensorRT-LLM uses **paged KV cache** by default, which breaks this notepad into fixed-size blocks (like memory pages in an OS), dynamically allocating and freeing them. This avoids wasting memory on pre-allocated buffers for maximum sequence lengths that most requests never reach.

### In-Flight Batching

**In-flight batching** (also called continuous batching) dynamically manages requests — like a restaurant that seats new diners as soon as a table frees up rather than waiting for the entire dining room to finish. Traditional static batching waits until all requests in a batch complete before starting new ones. In-flight batching processes prefill (the "reading the prompt" phase) and generation (the "writing tokens" phase) together, so a new request can start its prefill while existing requests are mid-generation.

### Quantization

**Quantization** reduces the numerical precision of model weights and activations — like compressing a high-resolution photo to JPEG: you lose some fidelity but use much less memory and compute. TensorRT-LLM supports [10+ quantization formats](https://nvidia.github.io/TensorRT-LLM/reference/precision.html): FP8 (Hopper GPUs), NVFP4 (Blackwell), INT8 SmoothQuant, INT4 AWQ, and more. FP8 quantization on H100 typically delivers 1.4-2.3x speedup with minimal quality loss.

### Plugins (Custom Kernels)

**Plugins** are custom CUDA kernels registered as TensorRT operations — like hand-tuned assembly subroutines called from a higher-level program. They handle operations where TensorRT's automatic optimization can't discover the best implementation: FlashAttention for the attention mechanism, NCCL-based all-reduce for multi-GPU communication, and specialized GEMM kernels for quantized matrix multiplies. These are written in C++ and live in `cpp/tensorrt_llm/plugins/`.

### Executor

The **Executor** is the runtime engine that orchestrates inference — like an air traffic controller managing incoming flights (requests), runway allocation (GPU resources), and departure sequencing (response delivery). It runs a continuous loop: fetch new requests, schedule them for execution, allocate KV cache blocks, run the forward pass, sample tokens, and deliver results. The C++ `Executor` provides the low-level API; the Python `PyExecutor` wraps it for the PyTorch path.

### How They Fit Together

A user initializes the **LLM API** with a model name. The **Builder** compiles the model into an optimized **Engine**, applying **Quantization** and inserting **Plugins** for specialized operations. At runtime, the **Executor** receives requests and uses **In-Flight Batching** to schedule them efficiently. As tokens are generated, the **KV Cache** stores intermediate results in paged memory blocks, and the Executor returns completed responses.

```
User Code → LLM API → Builder (compiles) → Engine (optimized binary)
                                                    ↓
Request → Executor → In-Flight Batching → Engine (forward pass)
                ↕                              ↕
          KV Cache (paged)              Plugins (kernels)
```
