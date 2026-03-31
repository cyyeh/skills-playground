## How It Works
<!-- level: intermediate -->
<!-- references:
- [MLflow Tracking Documentation](https://mlflow.org/docs/latest/tracking/) | official-docs
- [Automatic Logging with MLflow](https://mlflow.org/docs/latest/tracking/autolog/) | official-docs
- [MLflow Models Documentation](https://mlflow.org/docs/latest/ml/model/) | official-docs
- [MLflow Model Registry](https://mlflow.org/docs/latest/ml/model-registry/) | official-docs
-->

### Experiment Tracking

MLflow's tracking system works through a layered client-server architecture. When you write `mlflow.log_metric("accuracy", 0.95)`, several things happen beneath the surface:

1. The fluent API checks the thread-local context for an active run. If none exists, it auto-creates one using the active experiment (set via `mlflow.set_experiment()` or the `MLFLOW_EXPERIMENT_NAME` environment variable).

2. The metric is validated (key must be a string, value must be numeric, step must be an integer), then packaged into a protobuf message.

3. The `TrackingServiceClient` sends a REST API request to the tracking server at the configured tracking URI (`MLFLOW_TRACKING_URI`).

4. The tracking server's request handler deserializes the protobuf, routes the request to the backend store, and the `SqlAlchemyStore` executes an INSERT into both the `metrics` table (full history) and the `latest_metrics` table (fast lookups).

5. For metric deduplication, the store checks if an identical (run_id, key, timestamp, step, value) tuple already exists before inserting. The `latest_metrics` table is updated only if the new metric has a later timestamp or step than the existing latest entry.

MLflow supports both synchronous and asynchronous logging. Async logging (enabled via `MLFLOW_ENABLE_ASYNC_LOGGING=true` or `synchronous=False`) buffers log calls and sends them in batches, reducing network overhead for high-frequency logging. The batch API (`mlflow.log_metrics()`, `mlflow.log_params()`) is recommended for bulk operations.

### Autologging

Autologging is MLflow's "zero-code" tracking feature. When you call `mlflow.autolog()` or a framework-specific variant like `mlflow.sklearn.autolog()`, MLflow monkey-patches the training functions of supported ML libraries to automatically capture parameters, metrics, and models.

The mechanism works through the `autologging_integration` decorator and `safe_patch` utility:

1. **Registration:** Each supported library (scikit-learn, PyTorch, TensorFlow, XGBoost, etc.) has an autolog function decorated with `@autologging_integration("library_name")`. This registers the integration and stores its configuration.

2. **Patching:** When autologging is enabled, MLflow patches key methods on the ML framework. For scikit-learn, it patches `fit()`, `fit_transform()`, and `fit_predict()` on all estimators. For PyTorch, it patches the training loop. For LangChain, it patches `invoke()` and `__call__()`.

3. **Interception:** When the patched method is called (e.g., `model.fit(X, y)`), the patch wrapper automatically creates a run, logs relevant parameters (from the estimator's `get_params()`), logs metrics (from `score()`), and saves the trained model as an artifact.

4. **Safety:** The `safe_patch` mechanism ensures that autologging failures never break user code. If logging fails, it catches the exception, logs a warning, and lets the original function proceed normally.

The autologging configuration is stored in a global dictionary `AUTOLOGGING_INTEGRATIONS` protected by a thread-safe lock. Each integration can be independently enabled/disabled and configured with options like `log_models`, `log_datasets`, `log_input_examples`, and `silent`.

### Model Packaging (MLmodel Format)

When you call `mlflow.sklearn.log_model(model, "model")`, MLflow creates a standardized model package:

1. **Serialization:** The framework-specific module serializes the model. For scikit-learn, this uses `pickle` or `cloudpickle`. For PyTorch, `torch.save()`. For TensorFlow, `tf.saved_model.save()`.

2. **MLmodel File Generation:** MLflow creates an `MLmodel` YAML file describing the model:
   ```yaml
   artifact_path: model
   flavors:
     python_function:
       loader_module: mlflow.sklearn
       python_version: 3.10.12
       env: conda.yaml
     sklearn:
       pickled_model: model.pkl
       sklearn_version: 1.3.0
       serialization_format: cloudpickle
   signature:
     inputs: '[{"name": "feature1", "type": "double"}, ...]'
     outputs: '[{"type": "long"}]'
   model_uuid: a1b2c3d4-...
   ```

3. **Environment Capture:** MLflow generates `conda.yaml` and `requirements.txt` files listing the exact package versions used during training. This ensures the model can be loaded in an identical environment during serving.

4. **Artifact Upload:** The entire package (model file, MLmodel, conda.yaml, requirements.txt) is uploaded to the artifact store as a directory.

The key insight is the **flavor system**. A single model can have multiple flavors -- the `sklearn` flavor for native scikit-learn operations, and the `python_function` (pyfunc) flavor for generic inference. The pyfunc flavor is the universal interface: any MLflow model can be loaded as a pyfunc and called with `model.predict(data)`, regardless of the underlying framework. This is what enables framework-agnostic deployment.

### Model Registry Workflow

The model registry manages the lifecycle of production models through a state machine:

1. **Registration:** `mlflow.register_model(model_uri, "fraud-detector")` creates a `RegisteredModel` entry (if new) and a `ModelVersion` linked to the run's model artifact. The version number auto-increments.

2. **Aliasing:** Model versions can be assigned aliases like "champion" (the current best) and "challenger" (the candidate being evaluated). Aliases are mutable pointers -- reassigning "champion" to a new version is atomic.

3. **Stage Transitions:** The classic workflow uses stages: None -> Staging -> Production -> Archived. Each transition can be gated by organizational policies (automated tests, human review, performance thresholds).

4. **Version Comparison:** The registry UI and API let you compare metrics, parameters, and artifacts across model versions side by side. This supports data-driven promotion decisions.

5. **Deployment:** Production systems load models by alias or version: `mlflow.pyfunc.load_model("models:/fraud-detector@champion")`. When the alias moves to a new version, the next model load picks up the new version automatically.

The registry stores all version metadata (creation time, source run, description, tags) in the backend store. The model artifacts themselves remain in the artifact store -- the registry just stores a URI pointing to them. This avoids duplicating large model files.

### Model Serving and Deployment

MLflow provides multiple deployment paths:

**Local Serving:** `mlflow models serve -m models:/my-model/1 -p 5001` starts a REST API server wrapping the model. It creates a virtual environment from the model's conda.yaml, loads the model, and serves predictions on a `/invocations` endpoint.

**Docker Containerization:** `mlflow models build-docker -m models:/my-model/1 -n my-model-image` packages the model into a Docker image with all dependencies. The image includes a Gunicorn/Flask server ready for Kubernetes deployment.

**Batch Inference:** Load the model in a Spark job or Python script and call `model.predict()` on a dataset. The pyfunc interface accepts pandas DataFrames, numpy arrays, and Spark DataFrames.

**Cloud Deployment:** MLflow integrates with AWS SageMaker, Azure ML, and Databricks for managed model serving with auto-scaling, A/B testing, and monitoring.

### Performance Characteristics

**Where it excels:**
- Experiment tracking at scale -- the SQL backend handles millions of runs with efficient indexing on experiment_id, metric values, and parameters. Batch logging and async mode handle high-frequency metric streams without bottlenecking training.
- Model packaging -- the MLmodel format adds minimal overhead (a few YAML files) to the actual model serialization. Loading a model from the registry adds only the time to download artifacts from the artifact store.
- Framework agnosticism -- the pyfunc flavor means a single deployment pipeline works for any framework, reducing operational complexity.

**Where it's slower:**
- The tracking server adds network latency to every log call. For extremely high-frequency logging (thousands of metrics per second), consider batching or async mode.
- Large artifact uploads can be slow through the tracking server proxy. For multi-gigabyte models, configure direct artifact access to the underlying store (S3, GCS) to bypass the server.
- The file-based backend store (used by default) doesn't support concurrent writes well. Switch to a database-backed store for any team usage.
