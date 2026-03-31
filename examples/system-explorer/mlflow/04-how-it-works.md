## How It Works
<!-- level: intermediate -->
<!-- references:
- [MLflow Tracking API](https://mlflow.org/docs/latest/tracking/tracking-api) | docs
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry/) | docs
- [MLflow Deployment](https://mlflow.org/docs/latest/deployment/index.html) | docs
- [MLflow Tracing](https://mlflow.org/docs/latest/genai/tracing/) | docs
-->

### Workflow 1: Logging an Experiment

**Step 1 -- Set the tracking URI.** Point the client at a tracking server:

```python
import mlflow
mlflow.set_tracking_uri("http://my-tracking-server:5000")
```

**Step 2 -- Create or set an experiment.** Experiments group related runs:

```python
mlflow.set_experiment("fraud-detection-v2")
```

**Step 3 -- Start a run and log data.** Everything inside the `with` block is recorded:

```python
with mlflow.start_run():
    mlflow.log_param("learning_rate", 0.01)
    mlflow.log_param("n_estimators", 200)

    # ... training code ...

    mlflow.log_metric("accuracy", 0.943)
    mlflow.log_metric("f1_score", 0.917)
    mlflow.log_artifact("confusion_matrix.png")
    mlflow.sklearn.log_model(model, "model")
```

**Step 4 -- View results.** Open the MLflow UI (`http://my-tracking-server:5000`), navigate to the experiment, and compare runs side by side with metric charts, parameter tables, and artifact viewers.

**What happens under the hood:**
- `start_run()` sends a `POST /api/2.0/mlflow/runs/create` to the tracking server.
- Each `log_param`, `log_metric`, and `log_artifact` call sends its own REST request.
- The tracking server writes metadata to the backend store (database) and artifacts to the artifact store (e.g., S3).
- The UI queries the backend store and renders run comparisons.

### Workflow 2: Using Autologging

Instead of manual `log_param` and `log_metric` calls, autologging captures everything automatically:

```python
import mlflow
mlflow.autolog()

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y)
model = RandomForestClassifier(n_estimators=200, max_depth=10)
model.fit(X_train, y_train)
```

MLflow's autologging hooks into the library's `.fit()` method using monkey-patching. It automatically logs all constructor parameters, training metrics, the fitted model artifact, and (for supported libraries) feature importance plots and evaluation metrics.

Autologging supports 20+ libraries: scikit-learn, TensorFlow, Keras, PyTorch, XGBoost, LightGBM, CatBoost, Spark, Statsmodels, and more.

### Workflow 3: Registering a Model

**Step 1 -- Register from a run.** After training, promote a model to the registry:

```python
result = mlflow.register_model(
    model_uri="runs:/abc123def456/model",
    name="fraud-detector"
)
```

This creates a new version (e.g., version 3) of the registered model "fraud-detector," linked to the specified run.

**Step 2 -- Assign an alias.** Mark the new version as the production candidate:

```python
from mlflow import MlflowClient
client = MlflowClient()
client.set_registered_model_alias("fraud-detector", "champion", version=3)
```

**Step 3 -- Load by alias.** Downstream services load the model without hardcoding a version number:

```python
model = mlflow.pyfunc.load_model("models:/fraud-detector@champion")
predictions = model.predict(new_data)
```

### Workflow 4: Deploying a Model

**Option A -- Local REST server:**

```bash
mlflow models serve -m "models:/fraud-detector@champion" --port 5001
```

This starts a Flask server with a `/invocations` endpoint that accepts JSON or CSV input.

**Option B -- Docker container:**

```bash
mlflow models build-docker -m "models:/fraud-detector@champion" -n fraud-detector-image
docker run -p 5001:8080 fraud-detector-image
```

**Option C -- Cloud deployment (SageMaker):**

```python
mlflow.sagemaker.deploy(
    app_name="fraud-detector",
    model_uri="models:/fraud-detector@champion",
    region_name="us-west-2",
    mode="create"
)
```

**Option D -- Kubernetes (via Seldon Core or KServe):**

MLflow provides plugins that generate Kubernetes-native deployment manifests from MLflow models.

### Workflow 5: GenAI Tracing and Observability

Since MLflow 3.0, the platform includes comprehensive tracing for GenAI applications:

**Step 1 -- Enable tracing.** For supported libraries, tracing is automatic:

```python
import mlflow
mlflow.openai.autolog()  # or mlflow.langchain.autolog()
```

**Step 2 -- View traces.** Every LLM call, tool invocation, and retrieval step is captured as a span in a trace. The MLflow UI shows the full request lifecycle with inputs, outputs, latency, and token counts.

**Step 3 -- Evaluate.** Use built-in or custom scorers to evaluate agent quality:

```python
results = mlflow.evaluate(
    model=my_agent,
    data=eval_dataset,
    model_type="agent",
    evaluators=["correctness", "safety", "relevance"]
)
```

This runs each evaluation example through the agent, applies LLM judges, and produces a scored report with per-example and aggregate metrics.
