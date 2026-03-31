## How It Works
<!-- level: intermediate -->
<!-- references:
- [MLflow Tracking Internals](https://mlflow.org/docs/latest/ml/tracking/) | official-docs
- [MLflow Models, Flavors, and PyFuncs](https://mlflow.org/docs/latest/ml/traditional-ml/tutorials/creating-custom-pyfunc/part1-named-flavors/) | official-docs
- [MLflow Tracing Architecture](https://mlflow.org/docs/latest/genai/tracing/) | official-docs
- [MLflow LLM Evaluation](https://mlflow.org/docs/latest/genai/eval-monitor/) | official-docs
-->

### Tracking Engine

The tracking engine is the backbone of MLflow, responsible for persisting all experiment metadata. When a user calls `mlflow.start_run()`, the fluent API layer manages a thread-local stack of active runs. This design allows nested runs (a hyperparameter sweep containing individual training runs) while ensuring that concurrent threads in the same process do not interfere with each other.

**Run lifecycle management:** The `ActiveRun` context manager ensures runs are properly finalized even if exceptions occur. When used as `with mlflow.start_run():`, the context manager calls `end_run()` on exit, setting the status to `FINISHED` on normal exit or `FAILED` on exception. This prevents orphaned runs in `RUNNING` status that would clutter the experiment.

**Batch logging for efficiency:** Individual `log_metric()` calls each make a REST request to the tracking server. For performance-critical code logging hundreds of metrics per step, MLflow provides `log_batch()` which sends metrics, parameters, and tags in a single request. The `SqlAlchemyStore.log_batch()` implementation validates all data upfront, then persists params, metrics, and tags in separate batch insert operations within a single database transaction.

**Async logging:** When `MLFLOW_ENABLE_ASYNC_LOGGING` is enabled, logging calls return immediately with a `RunOperations` future, and data is flushed to the backend in background threads. This prevents metric logging from blocking training iterations, which is critical for high-frequency logging in deep learning where a single training step may take milliseconds but a REST roundtrip takes tens of milliseconds.

**Metric history and latest caching:** Every metric logged is appended to the `SqlMetric` table with its step and timestamp, preserving the full history for visualization. However, the most common query pattern is "show me the final value of each metric for all runs" (used by the run comparison UI and `search_runs`). To avoid expensive `GROUP BY` aggregations, MLflow maintains a separate `SqlLatestMetric` table that is updated on each `log_metric` call, trading a small write overhead for dramatically faster reads.

**Auto-logging:** MLflow provides auto-logging integrations for popular frameworks (scikit-learn, XGBoost, PyTorch, TensorFlow/Keras, Spark MLlib, and others). When you call `mlflow.autolog()`, MLflow monkey-patches the framework's training functions to automatically log parameters, metrics, and models without any explicit logging calls. For example, `mlflow.sklearn.autolog()` patches `sklearn.base.BaseEstimator.fit()` to log all estimator parameters and training metrics. Auto-logging uses a registry pattern where each framework registers its autolog function, and the global `mlflow.autolog()` activates all registered integrations.

### Model Packaging System

MLflow's model packaging is one of its most distinctive mechanisms. The system solves a fundamental problem: a trained model is useless without the exact code, dependencies, and configuration needed to load and run it.

**The MLmodel descriptor:** Every MLflow model directory contains an `MLmodel` YAML file that declares the model's flavors, signature, dependencies, and metadata. This file is the model's bill of materials. When any tool loads an MLflow model, it reads `MLmodel` first to determine how to proceed.

**Flavor resolution:** When you call `mlflow.pyfunc.load_model(uri)`, the loader reads the `MLmodel` file, finds the `python_function` flavor entry, extracts the `loader_module` field (e.g., `mlflow.sklearn`), dynamically imports that module, and calls its `_load_pyfunc()` function with the data path. This indirection is what makes the system extensible -- adding a new framework flavor only requires implementing `save_model`, `load_model`, and `_load_pyfunc` functions in a new module, plus registering the pyfunc loader.

**Dependency capture:** When a model is logged, MLflow automatically captures the Python environment: `requirements.txt` (pip packages), `conda.yaml` (conda environment), and `python_env.yaml` (virtualenv specification). During model loading in production, MLflow can recreate the exact environment using any of these specifications. The environment manager is pluggable -- you can use `virtualenv`, `conda`, or the newer `uv` (Rust-based, significantly faster). This automatic dependency capture is what makes models genuinely portable across machines.

**Model signature enforcement:** Models can declare a [signature](https://mlflow.org/docs/latest/ml/model/signatures/) specifying input schema, output schema, and inference parameters. When `PyFuncModel.predict()` is called, it validates the input against the declared schema using `_enforce_schema()`, coercing types where possible and raising errors on mismatches. This catches common issues (wrong column names, unexpected types) before they reach the model code, providing clear error messages instead of cryptic framework errors.

**Models from code:** MLflow 2.x introduced a "models from code" feature that avoids pickle/cloudpickle entirely. Instead of serializing a Python object, you define your model as a Python script that creates an instance of your `PythonModel` subclass and calls `mlflow.models.set_model()`. Loading the model executes the script in a fresh environment. This eliminates the security risks of deserializing untrusted pickled objects and makes model code reviewable as plain text.

### Model Registry Lifecycle

The model registry manages model versions through a structured lifecycle that bridges the gap between experimentation and production.

**Version creation:** When `mlflow.register_model()` is called, the `SqlAlchemyModelRegistryStore.create_model_version()` method inserts a new `SqlModelVersion` row with an auto-incremented version number and a `source` field pointing to the original run's artifact location. The model artifacts are not copied -- the version references the original location. This is efficient but means deleting the original run's artifacts breaks the registered model version.

**Alias-based promotion:** Instead of the older stage-based workflow (None -> Staging -> Production -> Archived), MLflow 3.x uses aliases as mutable pointers. An alias like `@champion` points to a specific version number. When you set `client.set_registered_model_alias("MyModel", "champion", version=5)`, the store atomically updates the alias mapping. Serving systems that load `models:/MyModel@champion` automatically pick up the new version on next load. This is more flexible than fixed stages because you can define arbitrary aliases (`@shadow`, `@canary`, `@region-eu`) tailored to your deployment strategy.

**Lineage tracking:** Every model version records the `run_id` that produced it, creating a chain from production model back to the exact experiment, code, data, and hyperparameters that created it. This lineage is critical for compliance (auditors need to know how a production model was built) and debugging (when a model starts underperforming, you can trace back to its training data and parameters).

### Tracing and Observability

MLflow's tracing system provides request-level observability for GenAI applications, built on OpenTelemetry.

**Dual-mode tracer provider:** The `TracerProviderWrapper` operates in two modes. In isolated mode (default), MLflow creates its own tracer provider instance, ensuring it does not interfere with any existing OpenTelemetry instrumentation in the application. In unified mode (activated by `MLFLOW_USE_DEFAULT_TRACER_PROVIDER`), MLflow integrates with the global OpenTelemetry provider, enabling distributed tracing across services. This dual-mode design reflects a practical reality: many teams already have OpenTelemetry set up, and MLflow must coexist without conflicts.

**Auto-tracing instrumentation:** For supported frameworks (OpenAI, Anthropic, LangChain, LlamaIndex, DSPy, Vercel AI SDK), a single call like `mlflow.openai.autolog()` patches the framework's client to automatically create spans for every LLM call. The patching captures inputs (prompts), outputs (completions), token usage, latency, and model identifiers. This works through framework-specific integration modules that understand each library's call patterns.

**Span hierarchy and context propagation:** Traces are trees of spans. The root span represents the entire request. Child spans represent individual steps: retrieval calls, prompt formatting, LLM invocations, tool executions, and post-processing. Context propagation through `set_span_in_context()` and `detach_span_from_context()` uses either MLflow's own `ContextVarsRuntimeContext` (isolated mode) or OpenTelemetry's standard context API (unified mode). This ensures parent-child relationships are correctly maintained even in async and multi-threaded applications.

**Async export for production:** In production, trace data is exported asynchronously to avoid adding latency to user-facing requests. Span processors collect completed spans and batch-export them to the configured destination (MLflow tracking server, OTLP endpoint, or Databricks inference tables). The lightweight `mlflow-tracing` package (95% smaller than full MLflow) is available for production deployments where you need tracing without the full MLflow SDK overhead.

### Evaluation Engine

MLflow provides a comprehensive evaluation framework, particularly powerful for GenAI applications.

**LLM judges:** MLflow ships with 50+ built-in [evaluation metrics and LLM judges](https://mlflow.org/docs/latest/genai/eval-monitor/) that assess different quality dimensions: safety, relevance, groundedness, correctness, and more. Each judge is a prompt template that uses an LLM to evaluate a trace or response. Custom judges can be defined through a flexible API. Judges provide not just scores but detailed rationales explaining their assessment.

**Continuous monitoring:** MLflow can automatically run LLM judges on incoming production traces without writing code. You configure which judges to apply, and the system evaluates every trace (or a sample), detecting quality regressions in real-time. Results are surfaced in dashboards showing quality trends over time.

**Evaluation from traces:** The system can create evaluation datasets directly from production traces, enabling teams to build test suites from real user interactions. This closes the loop between production monitoring and offline evaluation -- if you observe a quality issue in production, you can capture those cases, investigate them, and add them to your regression test suite.

### Performance Characteristics

**Tracking throughput:** The tracking server can handle hundreds of concurrent logging requests. The primary bottleneck is database write throughput. PostgreSQL backends with connection pooling handle production loads well. SQLite (default) is single-writer and becomes a bottleneck with concurrent runs.

**Artifact transfer:** Artifact upload/download speed is bounded by the artifact store's throughput. Direct S3 uploads from the client (proxy-free mode) achieve much higher throughput than routing through the tracking server. For multi-gigabyte models, this is a significant performance consideration.

**Model loading latency:** Loading a model involves downloading artifacts from the artifact store, optionally creating a virtual environment, and deserializing the model object. For a typical scikit-learn model, this takes seconds. For large deep learning models (multi-GB), it can take minutes. The `mlflow.pyfunc.load_model()` caching behavior varies by deployment context.

**Tracing overhead:** Auto-tracing adds approximately 1-5ms overhead per span in isolated mode. The async export path ensures trace data collection does not add to response latency. The `mlflow-tracing` lightweight package further reduces import time and memory footprint.

**Search query performance:** Run and experiment search uses SQL queries with parameterized filters. The `SqlLatestMetric` cache table makes metric-based filtering fast. Complex filter expressions with multiple metric and parameter conditions can be slow on large datasets without appropriate database indexes.
