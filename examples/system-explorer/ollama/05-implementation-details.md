## Implementation Details
<!-- level: advanced -->
<!-- references:
- [Ollama GitHub Repository](https://github.com/ollama/ollama) | github
- [Ollama API Reference](https://docs.ollama.com/api/) | official-docs
- [Ollama Modelfile Reference](https://docs.ollama.com/modelfile) | official-docs
- [GGUF Format Specification](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md) | github
-->

### Getting Started

Install Ollama and run your first model in under a minute:

```bash
# macOS
brew install ollama

# Linux (one-line installer)
curl -fsSL https://ollama.com/install.sh | sh

# Start the server (runs in background on macOS/Windows; manual on Linux)
ollama serve

# Pull and run a model
ollama run llama3.2
```

For Docker deployments with GPU support:

```bash
# NVIDIA GPU
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# CPU only
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Run a model via the container
docker exec -it ollama ollama run llama3.2
```

### Configuration Essentials

Ollama is configured primarily through environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_HOST` | `127.0.0.1:11434` | Server bind address |
| `OLLAMA_MODELS` | `~/.ollama/models` | Model storage directory |
| `OLLAMA_NUM_PARALLEL` | `0` (auto) | Max parallel requests per model |
| `OLLAMA_MAX_LOADED_MODELS` | `0` (auto) | Max models in memory simultaneously |
| `OLLAMA_KEEP_ALIVE` | `5m` | Idle model timeout before unloading |
| `OLLAMA_MAX_QUEUE` | `512` | Max queued requests before rejecting |
| `OLLAMA_FLASH_ATTENTION` | `0` | Enable flash attention (1 to enable) |
| `OLLAMA_KV_CACHE_TYPE` | `f16` | KV cache precision (f16, q8_0, q4_0) |
| `OLLAMA_GPU_OVERHEAD` | `0` | Reserved VRAM bytes not used for models |
| `OLLAMA_ORIGINS` | `localhost` | Allowed CORS origins |

Per-model parameters are set via the API or Modelfile:

```
FROM llama3.2
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
SYSTEM "You are a helpful coding assistant. Respond concisely."
```

### Code Patterns

**Python chat with streaming:**

```python
import requests
import json

def chat_stream(model, messages):
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={"model": model, "messages": messages, "stream": True},
        stream=True
    )
    for line in response.iter_lines():
        if line:
            chunk = json.loads(line)
            if "message" in chunk:
                print(chunk["message"]["content"], end="", flush=True)

chat_stream("llama3.2", [
    {"role": "user", "content": "Explain quicksort in 3 sentences"}
])
```

**Using the OpenAI-compatible API (drop-in replacement):**

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
response = client.chat.completions.create(
    model="llama3.2",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

**Tool calling:**

```python
import requests

response = requests.post("http://localhost:11434/api/chat", json={
    "model": "llama3.2",
    "messages": [{"role": "user", "content": "What's the weather in Tokyo?"}],
    "tools": [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            }
        }
    }],
    "stream": False
})
```

### Source Code Walkthrough

This section maps each core concept from the Core Concepts section to its actual implementation in the Ollama codebase.

#### Model Library -- Implementation

The Model Library concept is implemented through the Name type that parses model references. This is the entry point for all model operations -- every `ollama run` or API call starts by parsing the model name into its components (host, namespace, model, tag), with defaults filling in the Ollama registry and "latest" tag.

```go
// source: types/model/name.go
// github: ollama/ollama
// tag: v0.20.0
type Name struct {
	Host           string
	Namespace      string
	Model          string
	Tag            string
	ProtocolScheme string
}

// ParseName parses and assembles a Name from a name string.
// The format is: [host/][namespace/]model[:tag]
// Missing components are filled with defaults:
//   Host -> registry.ollama.ai
//   Namespace -> library
//   Tag -> latest
func ParseName(s string, fill FillKind) Name {
	var r Name
	// ... parsing logic works backward through the string:
	// 1. Last colon (after any slash) separates the tag
	// 2. Forward slashes separate host, namespace, and model
	// 3. Protocol schemes are detected via "://"
	return r
}

// DisplayShortest returns the shortest unambiguous form
// For models in the default registry: "llama3.2:latest" -> "llama3.2"
func (n Name) DisplayShortest() string { /* ... */ }
```

#### GGUF Format -- Implementation

The GGUF format concept is implemented in the convert package, where the `WriteGGUF` function handles serialization of model data into the binary format. The conversion pipeline reads tensors from SafeTensors or PyTorch files and writes them as GGUF, the format required by the inference runner.

```go
// source: convert/convert.go
// github: ollama/ollama
// tag: v0.20.0

// ConvertModel converts a model from SafeTensors/PyTorch to GGUF format.
// It reads config.json to determine architecture, then routes to the
// appropriate model-specific converter.
func ConvertModel(fsys fs.FS, ws io.WriteSeeker) error {
	// Step 1: Read model config to identify architecture
	bts, err := fs.ReadFile(fsys, "config.json")

	// Step 2: Route to architecture-specific converter
	// Supports 25+ architectures including:
	//   LlamaForCausalLM, MistralForCausalLM, GemmaForCausalLM,
	//   Qwen2ForCausalLM, Phi3ForCausalLM, etc.

	// Step 3: Parse tensors with architecture-specific name remapping
	ts, err := parseTensors(fsys, strings.NewReplacer(conv.Replacements()...))

	// Step 4: Load tokenizer vocabulary and special tokens
	// Step 5: Write GGUF binary output via ggml.WriteGGUF()
	return ggml.WriteGGUF(ws, kv, ts)
}
```

#### Quantization -- Implementation

Quantization is configured through the Runner options that get passed to the inference backend. The Options struct shows how quantization-related parameters (num_gpu for GPU layer count, use_mmap for memory mapping) flow from the API through to the runner.

```go
// source: api/types.go
// github: ollama/ollama
// tag: v0.20.0
type Options struct {
	Runner

	// Sampling parameters that control generation quality
	NumKeep          int      `json:"num_keep,omitempty"`
	Seed             int      `json:"seed,omitempty"`
	NumPredict       int      `json:"num_predict,omitempty"`
	TopK             int      `json:"top_k,omitempty"`
	TopP             float32  `json:"top_p,omitempty"`
	MinP             float32  `json:"min_p,omitempty"`
	Temperature      float32  `json:"temperature,omitempty"`
	RepeatPenalty    float32  `json:"repeat_penalty,omitempty"`
	PresencePenalty  float32  `json:"presence_penalty,omitempty"`
	FrequencyPenalty float32  `json:"frequency_penalty,omitempty"`
	Stop             []string `json:"stop,omitempty"`
}

// Runner controls hardware allocation for inference
type Runner struct {
	NumCtx    int   `json:"num_ctx,omitempty"`    // Context window size
	NumBatch  int   `json:"num_batch,omitempty"`  // Batch size for prompt processing
	NumGPU    int   `json:"num_gpu,omitempty"`    // Number of layers on GPU
	MainGPU   int   `json:"main_gpu,omitempty"`   // Primary GPU device index
	UseMMap   *bool `json:"use_mmap,omitempty"`   // Memory-map model file
	NumThread int   `json:"num_thread,omitempty"` // CPU thread count
}
```

#### Modelfile -- Implementation

The Modelfile concept connects to the model creation flow. The CLI's `CreateHandler` reads a Modelfile and sends it to the server, which parses the instructions (FROM, PARAMETER, SYSTEM, TEMPLATE) to build a model manifest with the appropriate layers.

```go
// source: cmd/cmd.go
// github: ollama/ollama
// tag: v0.20.0

// CLI command definitions using Cobra
// The "create" command handles Modelfile parsing and model building

// NewCLI builds the root command with all subcommands:
//   run     - Execute models interactively or with prompts
//   create  - Build custom models from Modelfiles
//   pull    - Fetch models from registries
//   push    - Upload models to registries
//   serve   - Launch the Ollama server
//   list    - Display available models with metadata
//   ps      - List currently running models
//   show    - Retrieve model information
//   stop    - Unload active models
//   copy    - Duplicate models locally
//   delete  - Remove models
func NewCLI() *cobra.Command {
	// The root command triggers an interactive TUI when called
	// without arguments, displaying available models
	// and integrations like VS Code, Claude, Cline, etc.
}
```

#### REST API -- Implementation

The REST API is implemented in the Server type's `GenerateRoutes` method, which wires up all HTTP endpoints using the Gin framework. This is where the Ollama-native API and OpenAI-compatible API are both registered.

```go
// source: server/routes.go
// github: ollama/ollama
// tag: v0.20.0

// GenerateRoutes sets up all HTTP endpoints.
// Routes are organized into three groups:
//   1. Ollama-native API (/api/*)
//   2. OpenAI-compatible API (/v1/*)
//   3. Health and version endpoints
func (s *Server) GenerateRoutes(rc *ollama.Registry) (http.Handler, error) {
	// Ollama-native endpoints
	// POST /api/generate  -> GenerateHandler  (text completion)
	// POST /api/chat      -> ChatHandler      (conversational)
	// POST /api/embed     -> EmbedHandler     (embeddings)
	// POST /api/pull      -> PullHandler      (download models)
	// POST /api/push      -> PushHandler      (upload models)
	// GET  /api/tags      -> ListHandler      (list models)
	// POST /api/show      -> ShowHandler      (model details)
	// DELETE /api/delete   -> DeleteHandler    (remove models)
	// POST /api/copy      -> CopyHandler      (duplicate models)

	// OpenAI-compatible endpoints (middleware adapts request/response format)
	// POST /v1/chat/completions  -> wraps ChatHandler
	// POST /v1/completions       -> wraps GenerateHandler
	// POST /v1/embeddings        -> wraps EmbedHandler
}
```

#### Scheduler -- Implementation

The Scheduler is the most complex component. Its `GetRunner` method is the entry point for every inference request -- it either returns a cached runner or queues the request for loading.

```go
// source: server/sched.go
// github: ollama/ollama
// tag: v0.20.0
type Scheduler struct {
	pendingReqCh  chan *LlmRequest   // Incoming load requests
	finishedReqCh chan *LlmRequest   // Completed request notifications
	expiredCh     chan *runnerRef    // Expired model timers
	unloadedCh    chan any           // VRAM recovery confirmations

	loadedMu sync.Mutex
	loaded   map[string]*runnerRef  // Currently loaded models

	// Injected dependencies for testing
	loadFn          func(/* ... */)
	newServerFn     func(/* ... */)
	getGpuFn        func() ml.SystemInfo
}

// runnerRef tracks a loaded model and its lifecycle
type runnerRef struct {
	refMu           sync.Mutex
	refCount        uint              // Active request count (prevents unload)
	llama           llm.LlamaServer   // Inference subprocess handle
	gpus            []ml.DeviceID     // Assigned GPU devices
	vramSize        uint64            // GPU memory consumption
	sessionDuration time.Duration     // Keep-alive timeout
	expireTimer     *time.Timer       // Fires when model should unload
	model           *Model
}

// findRunnerToUnload selects the best candidate for eviction:
// 1. Prefer idle runners (refCount == 0)
// 2. Among idle, pick shortest session duration
// 3. Break ties by model name (deterministic)
func (s *Scheduler) findRunnerToUnload() *runnerRef { /* ... */ }
```

#### Runner -- Implementation

The Runner concept maps to the LlamaServer interface and its concrete implementations. The interface defines the contract between the Scheduler and the inference subprocess, covering the full lifecycle from loading through inference to cleanup.

```go
// source: llm/server.go
// github: ollama/ollama
// tag: v0.20.0

// LlamaServer defines the contract for inference backends.
// Two implementations exist:
//   - llamaServer: legacy llama.cpp runner
//   - ollamaServer: new engine with MLX support
type LlamaServer interface {
	Load(ctx context.Context, systemInfo ml.SystemInfo,
		gpus []ml.DeviceInfo, requireFull bool) ([]ml.DeviceID, error)
	Ping(ctx context.Context) error
	WaitUntilRunning(ctx context.Context) error
	Completion(ctx context.Context, req CompletionRequest,
		fn func(CompletionResponse)) error
	Embedding(ctx context.Context, input string) ([]float32, int, error)
	Tokenize(ctx context.Context, content string) ([]int, error)
	Close() error
	MemorySize() (total, vram uint64)
	Pid() int
}

// llmServer is the shared base for both implementations
type llmServer struct {
	port         int           // Ephemeral port for subprocess HTTP
	cmd          *exec.Cmd    // Subprocess handle
	done         chan struct{} // Closed when process exits
	options      api.Options   // Inference parameters
	modelPath    string        // Path to GGUF file
	totalLayers  uint64        // Total model layers
	sem          *semaphore.Weighted // Parallelism limiter
}

// StartRunner spawns the inference subprocess
func StartRunner(ollamaEngine bool, modelPath string,
	gpuLibs []string, out io.Writer,
	extraEnvs map[string]string) (*exec.Cmd, int, error) {
	// 1. Allocate ephemeral TCP port
	// 2. Configure GPU environment variables
	// 3. Spawn subprocess with exec.Command
	// 4. Return command handle and port
}
```

### Deployment Considerations

**Memory sizing:** As a rule of thumb, a Q4_K_M quantized model needs approximately 0.6 GB per billion parameters for weights, plus KV cache overhead. A 7B model needs ~4.5 GB, a 13B model needs ~8 GB, and a 70B model needs ~40 GB. Plan for 10-20% overhead for KV cache at default context lengths.

**GPU vs CPU tradeoffs:** Models run 5-20x faster on GPU than CPU. If a model does not fully fit in VRAM, Ollama splits layers between GPU and CPU, which is slower than fully-GPU but faster than fully-CPU. The `OLLAMA_GPU_OVERHEAD` variable lets you reserve VRAM for other applications.

**Production hardening:** Set `OLLAMA_HOST=0.0.0.0:11434` for network access, configure `OLLAMA_ORIGINS` for CORS, use `OLLAMA_KEEP_ALIVE=-1` to keep models permanently loaded, and set `OLLAMA_MAX_LOADED_MODELS` to limit memory usage. Put a reverse proxy (nginx, Caddy) in front for TLS and authentication -- Ollama has no built-in auth.

**Monitoring:** Ollama exposes the `/api/ps` endpoint for listing running models and their GPU allocation. For deeper metrics, check the server logs (stdout or systemd journal on Linux). There is no built-in Prometheus/metrics endpoint as of v0.20.0.
