## Implementation Details
<!-- level: advanced -->
<!-- references:
- [MLflow REST API Reference](https://mlflow.org/docs/latest/rest-api.html) | docs
- [MLflow Plugins](https://mlflow.org/docs/latest/ml/plugins) | docs
- [MLflow Tracking Server Architecture](https://mlflow.org/docs/latest/self-hosting/architecture/tracking-server/) | docs
- [MLflow GitHub Source](https://github.com/mlflow/mlflow) | github
-->

### Storage Backends

#### Backend Store (Metadata)

MLflow uses SQLAlchemy as the ORM layer, which means any SQLAlchemy-compatible database works as a backend store. The connection is specified via a database URI:

```bash
mlflow server --backend-store-uri postgresql://user:pass@host:5432/mlflow
```

Supported backends:
| Backend | URI Format | Notes |
|---------|-----------|-------|
| SQLite | `sqlite:///mlflow.db` | Single-user, file-based. Good for dev. |
| PostgreSQL | `postgresql://...` | Recommended for production. |
| MySQL | `mysql://...` | Supported via PyMySQL or mysqlclient. |
| SQL Server | `mssql://...` | Supported via pyodbc. |
| File Store | `./mlruns` | Legacy default. No registry support. |

The database schema includes tables: `experiments`, `runs`, `params`, `metrics`, `tags`, `latest_metrics`, `registered_models`, `model_versions`, and `model_version_tags`.

Metrics are stored with a `step` and `timestamp`, allowing time-series visualization. The `latest_metrics` table caches the final value of each metric for fast query and sorting.

#### Artifact Store (Files)

Artifact storage is pluggable and completely separate from the metadata store:

```bash
mlflow server \
  --backend-store-uri postgresql://... \
  --default-artifact-root s3://my-bucket/mlflow-artifacts
```

Each run gets a unique artifact directory: `<artifact-root>/<experiment-id>/<run-id>/artifacts/`. The artifact store interface defines operations: `log_artifact`, `log_artifacts`, `list_artifacts`, `download_artifacts`.

When `--serve-artifacts` is enabled, the tracking server exposes an HTTP proxy at `/api/2.0/mlflow-artifacts/artifacts/`, so clients never need direct access to S3/Blob/GCS.

### REST API Design

The MLflow REST API follows a flat, resource-oriented design under `/api/2.0/mlflow/`:

**Key endpoints:**
- `POST /experiments/create` -- Create a new experiment
- `GET /experiments/get` -- Get experiment metadata
- `POST /runs/create` -- Start a new run
- `POST /runs/log-parameter` -- Log a single parameter
- `POST /runs/log-metric` -- Log a single metric
- `POST /runs/log-batch` -- Log params, metrics, and tags in batch
- `POST /runs/set-tag` -- Set a tag on a run
- `GET /runs/search` -- Search runs with filter expressions
- `POST /model-versions/create` -- Register a model version
- `GET /registered-models/search` -- Search registered models

The search API supports a SQL-like filter syntax:
```
metrics.accuracy > 0.9 AND params.model_type = 'random_forest'
```

All API responses use JSON. Request bodies are also JSON (or Protobuf for internal use). The API is versioned via the URL path (`/api/2.0/`).

### Client Libraries

**Python (`mlflow` package):** The primary client. Provides high-level fluent API (`mlflow.log_param()`, `mlflow.start_run()`), lower-level `MlflowClient` class, and framework-specific modules (`mlflow.sklearn`, `mlflow.pytorch`, etc.).

**R (`mlflow` CRAN package):** Wraps the REST API for R users. Supports tracking, model logging, and model serving.

**Java (`mlflow-client`):** A Java client for JVM-based workflows, commonly used with Spark MLlib.

**REST API:** Any language can interact with MLflow via HTTP. The REST API is the universal interface.

### Plugin System

MLflow provides extension points for custom integrations:

**Tracking Store Plugins:** Implement a custom backend store by extending `AbstractStore`. Use case: proprietary databases or cloud-specific metadata stores.

**Artifact Repository Plugins:** Extend `ArtifactRepository` to support custom file storage (e.g., a corporate artifact manager).

**Model Registry Store Plugins:** Custom registry implementations for specialized governance requirements.

**Deployment Plugins:** Define custom deployment targets by implementing the `BaseDeploymentClient` interface. Enables `mlflow deployments create -t <target>`.

**Model Evaluation Plugins:** Custom evaluator functions for domain-specific metrics.

Plugins are registered via Python entry points in `setup.py` or `pyproject.toml`:
```python
entry_points={
    "mlflow.artifact_repository": [
        "mystore=my_package.store:MyArtifactRepository"
    ]
}
```

### Autologging Implementation

Autologging uses **monkey-patching** to intercept framework method calls. When you call `mlflow.autolog()`, MLflow:

1. Detects which ML libraries are importable.
2. For each supported library, patches the `.fit()` (or equivalent training) method.
3. Before `.fit()` executes, the patch starts an MLflow run and logs constructor parameters.
4. After `.fit()` completes, the patch logs training metrics, the fitted model, and any framework-specific artifacts (e.g., feature importance for tree models).
5. The patch restores the original method signature, so the user's code is unaffected.

This is implemented in `mlflow/utils/autologging_utils/` with a `safe_patch` decorator that handles exceptions gracefully -- if logging fails, the training code still runs.

### Model Serialization

MLflow models are stored as a directory containing:
- `MLmodel` -- YAML file listing flavors, signatures, and metadata.
- `model.pkl` (or framework-specific format) -- The serialized model.
- `conda.yaml` / `requirements.txt` -- Environment dependencies.
- `python_env.yaml` -- Python version and environment specification.

Since MLflow 3.10, **pickle-free serialization** is supported using `torch.export` (PyTorch) and `skops` (scikit-learn), with a `MLFLOW_ALLOW_PICKLE_DESERIALIZATION` flag to control whether pickle-based models can be loaded (a security measure).

### Model Signatures and Input Examples

Models can include a **signature** that defines the expected input/output schema:

```python
from mlflow.models import infer_signature
signature = infer_signature(X_train, model.predict(X_train))
mlflow.sklearn.log_model(model, "model", signature=signature)
```

The signature is stored in the `MLmodel` file and enforced at serving time, rejecting malformed input before it reaches the model.
