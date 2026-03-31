## Implementation Details
<!-- level: advanced -->
<!-- references:
- [MLflow Tracking APIs](https://mlflow.org/docs/latest/tracking/tracking-api) | official-docs
- [MLflow Python API Reference](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.html) | official-docs
- [MLflow Self-Hosting Guide](https://mlflow.org/docs/latest/self-hosting/architecture/overview/) | official-docs
- [MLflow Troubleshooting](https://mlflow.org/docs/latest/self-hosting/troubleshooting/) | official-docs
-->

### Getting Started

Install MLflow and run your first tracked experiment:

```bash
pip install mlflow

# Start the tracking UI (optional -- MLflow works without a server)
mlflow ui --port 5000
```

```python
import mlflow

# Set the tracking URI (defaults to local ./mlruns)
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("my-first-experiment")

with mlflow.start_run():
    mlflow.log_param("learning_rate", 0.01)
    mlflow.log_param("epochs", 100)

    for epoch in range(100):
        loss = train_one_epoch(model, data)
        mlflow.log_metric("loss", loss, step=epoch)

    mlflow.sklearn.log_model(model, "model")
```

### Autologging Setup

```python
import mlflow

# Enable autologging for ALL supported frameworks
mlflow.autolog()

# Or enable for a specific framework with configuration
mlflow.sklearn.autolog(
    log_input_examples=True,
    log_model_signatures=True,
    log_models=True,
    log_datasets=True,
    silent=False,
)
```

### Production Tracking Server Deployment

```bash
# PostgreSQL backend + S3 artifact store + artifact proxy
mlflow server \
    --backend-store-uri postgresql://user:pass@db-host:5432/mlflow \
    --artifacts-destination s3://my-mlflow-bucket/artifacts \
    --serve-artifacts \
    --host 0.0.0.0 \
    --port 5000
```

Key configuration flags:
- `--backend-store-uri`: Database connection string (PostgreSQL recommended for production)
- `--artifacts-destination`: Remote artifact store location
- `--serve-artifacts`: Enable artifact proxying through the tracking server
- `--gunicorn-opts "--workers 4 --timeout 120"`: Tune the WSGI server for production load

### Docker Deployment

```dockerfile
FROM python:3.11-slim
RUN pip install mlflow psycopg2-binary boto3
EXPOSE 5000
CMD ["mlflow", "server", \
     "--backend-store-uri", "postgresql://...", \
     "--artifacts-destination", "s3://...", \
     "--serve-artifacts", \
     "--host", "0.0.0.0", "--port", "5000"]
```

### Model Registration and Serving

```python
import mlflow

# Register a model from an existing run
model_uri = "runs:/<run-id>/model"
mlflow.register_model(model_uri, "churn-predictor")

# Set model alias for production
from mlflow import MlflowClient
client = MlflowClient()
client.set_registered_model_alias("churn-predictor", "champion", version=3)

# Load model by alias in production code
model = mlflow.pyfunc.load_model("models:/churn-predictor@champion")
predictions = model.predict(new_data)
```

```bash
# Serve a model as a REST endpoint
mlflow models serve -m "models:/churn-predictor@champion" --port 8080

# Invoke the endpoint
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"inputs": [[5.1, 3.5, 1.4, 0.2]]}'
```

### GenAI Tracing Setup

```python
import mlflow

# Auto-tracing for OpenAI (one line)
mlflow.openai.autolog()

# Manual tracing with decorators
@mlflow.trace
def my_agent(question: str) -> str:
    context = retrieve_documents(question)
    return generate_answer(question, context)

# Access trace data programmatically
traces = mlflow.search_traces(experiment_ids=["1"])
```

### AI Gateway Configuration

```python
from mlflow.gateway import MlflowGatewayClient

# Create a route
client = MlflowGatewayClient("http://gateway:5001")
client.create_route(
    name="gpt4-chat",
    route_type="llm/v1/chat",
    model={
        "name": "gpt-4",
        "provider": "openai",
        "config": {"openai_api_key": "$OPENAI_API_KEY"}
    }
)
```

### Performance Tuning

- **Async logging:** Call `mlflow.config.enable_async_logging(True)` to log metrics/params without blocking the training loop.
- **Batch logging:** Use `mlflow.log_metrics()` (plural) and `mlflow.log_params()` to batch multiple values in a single API call.
- **Database indexing:** Ensure your PostgreSQL backend has indexes on `runs.experiment_id`, `metrics.run_uuid`, and `params.run_uuid` for fast queries.
- **Artifact cleanup:** Use `mlflow gc` or the MlflowClient to delete old runs and reclaim artifact storage.
- **Worker scaling:** Run the tracking server behind Gunicorn with 4-8 workers per CPU core for production concurrency.

### Source Code Structure

The MLflow repository is organized as:
- `mlflow/tracking/` -- Client-side tracking API and backend store implementations
- `mlflow/store/` -- Backend store (SQL, file) and artifact store (S3, GCS, Azure) implementations
- `mlflow/models/` -- Model packaging, flavors, and signature logic
- `mlflow/server/` -- Tracking server (FastAPI app, REST handlers)
- `mlflow/gateway/` -- AI Gateway server and route management
- `mlflow/tracing/` -- GenAI tracing instrumentation and OpenTelemetry integration
- `mlflow/pyfunc/` -- The universal python_function model flavor
- `mlflow/recipes/` -- MLflow Recipes (formerly Pipelines) for opinionated ML workflows
