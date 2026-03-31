## Core Concepts
<!-- level: beginner -->
<!-- references:
- [MLflow Concepts](https://mlflow.org/docs/latest/tracking/) | official-docs
- [MLflow Model Registry](https://mlflow.org/docs/latest/ml/model-registry/) | official-docs
- [MLflow Models Documentation](https://mlflow.org/docs/latest/ml/) | official-docs
- [MLflow GenAI Features](https://mlflow.org/docs/latest/genai/index.html) | official-docs
-->

### Experiments & Runs

**Definition:** An Experiment is a named container that groups related ML training runs. A Run is a single execution of ML code -- it captures everything about one attempt: the code version, parameters, metrics over time, and output artifacts.

**Analogy:** Think of an experiment as a lab notebook for a research question ("Which model architecture works best for churn prediction?"). Each run is a page in that notebook -- one set of knobs turned, one set of measurements recorded.

**Why it matters:** Without structured experiments, teams lose track of what they tried, what worked, and why. Experiments and runs create an auditable, searchable history so you can compare any two attempts side by side, weeks or months later.

### Parameters, Metrics & Artifacts

**Definition:** Parameters are input configuration values (learning rate, batch size, number of trees). Metrics are output measurements (accuracy, loss, F1 score) that can be logged at each training step. Artifacts are output files (trained model weights, plots, data snapshots) stored alongside the run.

**Analogy:** In a cooking experiment, parameters are your recipe (ingredients and temperatures), metrics are your taste scores, and artifacts are the actual dishes and photos you produced.

**Why it matters:** This triple -- inputs, measurements, outputs -- is the minimum information needed to reproduce and evaluate any ML experiment. MLflow logs them in a structured, queryable store so you never lose the connection between "what I configured" and "what I got."

### MLflow Tracking

**Definition:** MLflow Tracking is the logging and querying subsystem. It provides a Python/R/Java/REST API to log parameters, metrics, and artifacts during training, plus a web UI for visual exploration, comparison, and search across all runs.

**Analogy:** Tracking is the lab's record-keeping system -- every scientist (data scientist) writes their observations in the same format, and anyone can search and compare results on the shared dashboard.

**Why it matters:** Tracking is typically the first MLflow component teams adopt. It replaces ad-hoc spreadsheets, scattered CSV files, and "I think the best model was in that Jupyter notebook from last Tuesday" with a centralized, versioned, programmatically accessible experiment store.

### MLflow Projects

**Definition:** An MLflow Project is a standard format for packaging reusable, reproducible ML code. A project is simply a directory (or Git repo) with an MLproject file that declares entry points, parameters, and environment dependencies (Conda, Docker, or system).

**Analogy:** Think of a Project as a recipe card that not only lists ingredients (parameters) and steps (entry points) but also specifies the exact kitchen setup (environment) needed -- down to the brand of oven (Docker image) or spice rack (Conda environment).

**Why it matters:** Projects solve the "works on my machine" problem. Any team member can run `mlflow run <project-uri>` and get a bit-for-bit reproducible execution environment, whether the project lives in a Git repo, a local folder, or an S3 bucket.

### MLflow Models

**Definition:** An MLflow Model is a standard packaging format that bundles a trained model with metadata describing multiple "flavors" -- different ways to load the model. For example, a scikit-learn model can be loaded as a generic Python function, as a native sklearn object, or served as a REST endpoint.

**Analogy:** A Model is like a universal power adapter for your trained model. You train it once, and the multi-flavor packaging lets you plug it into different deployment targets (batch scoring, REST API, Spark UDF, edge device) without rewriting anything.

**Why it matters:** The model flavor system decouples training from serving. Data scientists train models with their preferred framework (PyTorch, TensorFlow, XGBoost, LightGBM, etc.), and operations teams deploy them through a uniform interface, regardless of the underlying framework.

### Model Registry

**Definition:** The Model Registry is a centralized store for managing the full lifecycle of MLflow Models. It provides model versioning, stage transitions (e.g., Staging to Production), model aliases (e.g., @champion), annotations, and lineage back to the originating experiment run.

**Analogy:** If MLflow Models is the universal adapter, the Model Registry is the equipment library. When a new version arrives, it gets cataloged, labeled, and shelved. Before it goes to the factory floor (production), a librarian (governance process) must sign off.

**Why it matters:** In production settings, you need to know exactly which model version is serving traffic, who promoted it, and what experiment produced it. The registry provides this audit trail and prevents unvetted models from reaching production.

### MLflow Tracing (GenAI)

**Definition:** MLflow Tracing provides end-to-end observability for GenAI applications. It automatically captures every LLM call, tool invocation, and retrieval step in agent workflows, linking traces to the exact code, data, and prompts that generated them. It supports auto-tracing for 20+ frameworks including OpenAI, Anthropic, LangChain, and LlamaIndex.

**Analogy:** Tracing is like a flight recorder for your AI agent. Every decision the agent makes -- every API call, every tool use, every retrieval -- gets logged with timestamps and context, so when something goes wrong (or right), you can replay the entire sequence.

**Why it matters:** LLM applications are non-deterministic and multi-step. Without tracing, debugging why an agent gave a bad answer requires guesswork. Tracing gives you full visibility into token costs, latency, and the decision chain, in both development and production.

### AI Gateway

**Definition:** The MLflow AI Gateway provides a unified, governed endpoint for accessing multiple LLM providers (OpenAI, Anthropic, Azure OpenAI, etc.). It handles credential management, rate limiting, request routing, cost tracking, and automatic trace capture for every request.

**Analogy:** The AI Gateway is like a corporate switchboard for LLM calls. Instead of every team dialing providers directly (and managing their own API keys and billing), they call through the switchboard, which handles routing, logging, and cost control centrally.

**Why it matters:** As organizations scale LLM usage, managing API keys, tracking costs per team, enforcing rate limits, and maintaining observability across multiple providers becomes critical. The gateway centralizes all of this in one governed layer.
