## Common Q&A
<!-- level: all -->
<!-- references:
- [MLflow Official Documentation](https://mlflow.org/docs/latest/) | official-docs
- [MLflow GitHub Issues](https://github.com/mlflow/mlflow/issues) | github
-->

### Q: How does MLflow handle concurrent writes from multiple training jobs?

The tracking server serializes writes through the backend store. For database-backed stores (PostgreSQL, MySQL), concurrent writes from multiple training jobs work correctly -- the database handles transaction isolation. Each `log_metric`, `log_param`, and `log_artifact` call is an independent operation, so there's no conflict as long as different runs use different run IDs (which they always do, since run IDs are UUIDs).

The main concurrency concern is the file-based backend store (the default). It uses filesystem operations without proper locking, so concurrent writes from multiple processes can corrupt data. For any team or production use, always use a database-backed store.

For artifact uploads, the tracking server can act as a proxy (serializing uploads through the server) or clients can upload directly to the artifact store (S3, GCS). Direct uploads scale better because the tracking server doesn't become a bottleneck for large file transfers.

### Q: What's the best way to organize experiments for a large team?

Use a naming convention that encodes project, model type, and owner: `team-name/project-name/model-type` (e.g., `fraud-team/transaction-scoring/xgboost`). MLflow experiments are flat (no hierarchy), so the naming convention provides logical grouping.

For large organizations, consider one experiment per model being developed, not per person. This concentrates all related runs in one place, making cross-person comparisons easy. Use tags to annotate runs with the author, branch, and purpose (e.g., `mlflow.set_tag("author", "alice")`, `mlflow.set_tag("purpose", "feature-engineering-v2")`).

For multi-team setups, use separate MLflow instances or a managed service (Databricks) with workspace isolation. This prevents experiment namespace conflicts and provides access control boundaries.

### Q: How should I handle large model artifacts (multi-GB models)?

Configure the artifact store to use object storage (S3, GCS, Azure Blob) instead of the local filesystem. For very large models (multi-GB), configure the tracking server for artifact proxying or direct client-to-store uploads to avoid routing everything through the server.

MLflow does not deduplicate artifacts across runs. If you log the same large model in 100 runs, you get 100 copies. To save storage, consider logging only the best models (based on a validation metric threshold) rather than every run. Alternatively, log model checkpoints selectively -- save only at significant improvements rather than every epoch.

For extremely large models (LLMs with tens of GB), consider logging a reference (URI) to the model stored elsewhere rather than uploading through MLflow. Use `mlflow.log_param("model_path", "s3://...")` for tracking and manage the model file separately.

### Q: How does autologging interact with custom logging? Can I use both?

Yes. Autologging and manual logging coexist within the same run. Autologging captures framework-specific parameters and metrics automatically, and your manual `mlflow.log_param()` and `mlflow.log_metric()` calls add additional information to the same run.

The only conflict to watch for is duplicate parameter names. If autologging logs a parameter called `learning_rate` and you also call `mlflow.log_param("learning_rate", value)` with a different value, you'll get an error (parameters are immutable). To avoid this, either rely on autologging for framework parameters and use manual logging for custom metrics, or disable specific aspects of autologging (e.g., `mlflow.sklearn.autolog(log_models=False)` to handle model logging yourself).

### Q: How do I migrate from file-based to database-backed storage?

There is no built-in migration tool. The recommended approach is:

1. Start a new tracking server with a database backend (`--backend-store-uri postgresql://...`).
2. Use the MLflow API to export runs from the old file store and import them into the new database store. The `mlflow.search_runs()` API can read from one tracking URI, and `MlflowClient` can write to another.
3. For artifacts, keep the old artifact store accessible or copy artifacts to the new location.

For production migrations, the community `mlflow-export-import` tool automates this process. It handles experiments, runs, parameters, metrics, tags, and artifacts.

The key lesson: start with a database-backed store from the beginning for any team use. The file store is only appropriate for individual development on a local machine.

### Q: How does MLflow compare to experiment tracking in Jupyter notebooks?

Jupyter notebooks are execution environments; MLflow is a tracking system. They are complementary, not alternatives. The problem with tracking experiments in notebooks alone is:

1. **Lost state:** When you re-run cells or restart the kernel, previous results disappear. MLflow persists everything to a backend store.
2. **No comparison:** Comparing results across notebook runs requires manual effort. MLflow's UI provides side-by-side comparison, charts, and filtering.
3. **No sharing:** Notebooks are files on one person's machine. MLflow's server makes experiments accessible to the whole team.
4. **No reproducibility:** A notebook doesn't capture the exact environment, parameters, and data version. MLflow logs all of these.

The best practice is to develop in notebooks and use MLflow to track results: add `mlflow.log_param()`, `mlflow.log_metric()`, and `mlflow.log_model()` calls to your notebook cells. This gives you the interactive development experience of notebooks with the systematic tracking of MLflow.

### Q: What happens if the tracking server goes down during training?

If you're using the fluent API with a remote tracking server and the server becomes unreachable, log calls will fail with a connection error. By default, this raises an exception that can interrupt your training.

To handle this gracefully:
1. **Async logging:** Enable `MLFLOW_ENABLE_ASYNC_LOGGING=true`. Async mode buffers log calls and retries on failure, reducing the impact of transient server outages.
2. **Local fallback:** Set `MLFLOW_TRACKING_URI` to a local directory as a fallback. Train with local tracking, then import the runs to the server later.
3. **Resilient wrapper:** Wrap MLflow calls in try/except blocks so logging failures don't crash training.
4. **High availability:** Run multiple tracking server instances behind a load balancer with a shared database backend. The stateless server design supports this directly.

The model itself is unaffected -- training continues regardless of tracking failures. The risk is losing the metadata for that run.

### Q: How do I implement A/B testing with MLflow model registry?

The model registry provides the version management layer for A/B testing, but the traffic routing itself happens in your serving infrastructure.

A common pattern:
1. Register two model versions: assign alias "champion" to the current best and "challenger" to the new candidate.
2. In your serving layer (load balancer, API gateway, or custom code), route a percentage of traffic to each version based on the alias.
3. Log prediction outcomes and business metrics to compare performance.
4. If the challenger wins, reassign the "champion" alias to it. This is an atomic operation in MLflow.

```python
from mlflow import MlflowClient
client = MlflowClient()

# Load both models
champion = mlflow.pyfunc.load_model("models:/fraud-detector@champion")
challenger = mlflow.pyfunc.load_model("models:/fraud-detector@challenger")

# Route traffic (simplified)
import random
model = challenger if random.random() < 0.1 else champion  # 10% to challenger
prediction = model.predict(features)
```

### Q: What are the practical scaling limits of a self-hosted MLflow server?

Based on community experience:
- **Runs:** A single PostgreSQL-backed instance handles millions of runs across thousands of experiments. Query performance depends on index optimization -- ensure indexes on experiment_id, run_uuid, and metric key columns.
- **Metrics per run:** Hundreds of thousands of metric data points per run are supported. The `latest_metrics` table provides fast lookups regardless of history depth.
- **Concurrent users:** The tracking server is stateless, so you can scale horizontally behind a load balancer. A single Gunicorn instance with 4 workers handles ~100 concurrent logging clients.
- **Artifacts:** Artifact storage scales with the underlying object store (S3, GCS). The tracking server is only a bottleneck if you're proxying artifacts through it -- configure direct artifact access for large files.
- **Model registry:** Handles thousands of registered models with hundreds of versions each. The main limitation is UI performance when listing many versions.

For organizations with thousands of data scientists, Databricks' managed MLflow provides additional scaling optimizations, access control, and Unity Catalog integration.
