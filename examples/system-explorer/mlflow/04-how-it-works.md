## How It Works
<!-- level: intermediate -->
<!-- references:
- [MLflow Tracking APIs](https://mlflow.org/docs/latest/tracking/tracking-api) | official-docs
- [Model Registry Workflows](https://mlflow.org/docs/latest/ml/model-registry/workflow/) | official-docs
- [LLM Tracing](https://mlflow.org/docs/latest/genai/tracing/) | official-docs
- [MLflow Python API](https://mlflow.org/docs/latest/python_api/mlflow.html) | official-docs
-->

### How Experiment Tracking Works

When you call `mlflow.start_run()`, the client creates a Run entity in the backend store via the tracking server's REST API. The run gets a unique UUID and is associated with an experiment. As training progresses, `mlflow.log_param()`, `mlflow.log_metric()`, and `mlflow.log_artifact()` send data to the server:

1. **Parameters** are stored as key-value pairs in the backend database, written once per run.
2. **Metrics** support step-based logging -- you can log accuracy at each epoch, and MLflow stores the full time series, enabling metric history plots in the UI.
3. **Artifacts** are uploaded to the artifact store (S3, GCS, local filesystem). The backend store only records the artifact URI, not the artifact content itself.
4. **Tags** provide free-form metadata (e.g., `mlflow.runName`, `mlflow.source.type`) for filtering and search.

The tracking server batches metric writes and uses async logging (when enabled) to minimize overhead on the training loop. The MLflow UI queries the same REST API to render experiment dashboards, run comparisons, and metric charts.

### How Autologging Works

When you call `mlflow.autolog()`, MLflow monkey-patches supported ML libraries (scikit-learn, PyTorch, TensorFlow, XGBoost, LightGBM, Spark MLlib, and 20+ others) to automatically intercept `fit()`, `train()`, and similar calls. The patches inject logging calls that capture:

- Training parameters (hyperparameters passed to the model constructor)
- Training metrics (loss, accuracy at each epoch for deep learning)
- The trained model as an artifact (in the appropriate MLflow model flavor)
- Input data signatures and examples (if enabled)

Autologging reduces integration effort to a single line of code. Framework-specific autologgers can be configured independently -- for example, `mlflow.openai.autolog()` captures traces by default but can optionally log input/output examples.

### How Model Packaging Works

When you call `mlflow.sklearn.log_model(model, "my_model")`, MLflow:

1. Serializes the model using the framework's native format (e.g., `pickle` for sklearn, `torch.save` for PyTorch).
2. Creates an `MLmodel` YAML descriptor that lists available "flavors" -- different interfaces for loading the model. A typical sklearn model has two flavors: `python_function` (generic) and `sklearn` (native).
3. Generates a `conda.yaml` and `requirements.txt` that pin the exact library versions used during training.
4. Optionally records an input signature (column names and types) and a sample input for validation.
5. Uploads the entire directory to the artifact store as a single artifact.

The multi-flavor system means deployment tools can choose how to load the model. A REST serving endpoint uses the `python_function` flavor; a Spark batch job uses the `spark` flavor; a mobile deployment might use the `onnx` flavor.

### How the Model Registry Works

Once a model is logged, you can register it in the Model Registry:

1. `mlflow.register_model()` creates a RegisteredModel entry (if new) and a new ModelVersion linked to the logged artifact.
2. Each version maintains lineage: the run ID, experiment ID, and artifact path that produced it.
3. Model aliases (e.g., `@champion`, `@challenger`) provide stable references that decouple consumers from version numbers. Promoting a new model to production means reassigning the `@champion` alias.
4. Tags and descriptions provide human-readable context for governance and auditing.
5. Downstream systems query the registry for the `@champion` version, ensuring they always get the approved model without code changes.

### How Tracing Works (GenAI)

MLflow Tracing instruments GenAI applications using OpenTelemetry-compatible spans:

1. Auto-tracing patches supported libraries (OpenAI, Anthropic, LangChain, etc.) to automatically wrap every LLM call, tool invocation, and retrieval step in a trace span.
2. Each span records inputs, outputs, latency, token counts, and cost metadata.
3. Spans are nested to reflect the call hierarchy -- an agent trace might contain spans for the orchestrator, a retrieval tool, and multiple LLM calls.
4. Traces are linked to the MLflow experiment and run context, providing full lineage from a production trace back to the code version and configuration that produced it.
5. Context propagation supports distributed tracing across microservices, so a trace can span multiple services in an agent architecture.

### How Model Serving Works

MLflow models can be served as REST endpoints via `mlflow models serve`:

1. The serving process loads the model using its `python_function` flavor.
2. It starts a Flask/FastAPI server exposing `/invocations` and `/ping` endpoints.
3. Input data is validated against the model's recorded signature.
4. For production deployments, MLflow integrates with serving platforms: Docker containers, Kubernetes, AWS SageMaker, Azure ML, and Databricks Model Serving.
5. Model aliases in the registry allow zero-downtime model swaps -- updating the `@champion` alias automatically routes traffic to the new version.
