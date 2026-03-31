## Common Q&A
<!-- level: all -->
<!-- references:
- [MLflow Troubleshooting & FAQs](https://mlflow.org/docs/latest/self-hosting/troubleshooting/) | official-docs
- [MLflow Best Practices](https://www.asigmo.com/post/mlflow-best-practices-and-lessons-learned) | blog
- [MLflow GitHub Issues](https://github.com/mlflow/mlflow/issues) | github
-->

### Q1: Should I use the file-based backend store or a database?

For anything beyond solo experimentation, use a database backend (PostgreSQL recommended). The default SQLite/file-based store lacks concurrent access support, has no proper indexing, and becomes the primary bottleneck for UI performance and query speed as experiments grow. The migration is straightforward: `mlflow server --backend-store-uri postgresql://...`.

### Q2: How do I handle model dependencies in production?

MLflow automatically captures `conda.yaml` and `requirements.txt` during model logging. However, relying solely on auto-captured dependencies is risky. Best practice: pin exact versions, test the model in an isolated environment before registering, and use Docker-based serving (`mlflow models build-docker`) for full environment reproducibility. For models with system-level dependencies (CUDA, C libraries), a custom Docker base image is essential.

### Q3: What's the difference between model stages and model aliases?

Model stages (Staging, Production, Archived) were the original lifecycle mechanism but are now deprecated. Model aliases (e.g., `@champion`, `@challenger`) are the recommended replacement. Aliases are more flexible: you can define arbitrary alias names, reassign them atomically, and a single model version can have multiple aliases. Stages were limited to a fixed set and had issues with concurrent transitions.

### Q4: How do I scale the tracking server for large teams?

Run the tracking server behind a reverse proxy (Nginx) with Gunicorn workers (4-8 per CPU core). Use a PostgreSQL backend with connection pooling (PgBouncer). Enable async logging on the client side (`mlflow.config.enable_async_logging(True)`) to reduce training overhead. For artifact-heavy workloads, use the artifact proxy mode to centralize access control. Monitor the server with standard observability tools (Prometheus metrics, access logs).

### Q5: How does MLflow compare to just using TensorBoard?

TensorBoard excels at visualizing training curves for a single experiment (especially for TensorFlow/PyTorch). MLflow operates at a higher level: it manages multiple experiments, compares runs, versions models, and tracks the full lifecycle to production. Many teams use both -- TensorBoard for deep-dive training visualization, MLflow for experiment management and production governance. They are complementary, not competing.

### Q6: Can MLflow track distributed training jobs?

Yes, but with nuance. For data-parallel training (PyTorch DDP, Horovod), log from only one process (typically rank 0) to avoid duplicate entries. For different experiments running on different nodes, each node can log to the same remote tracking server. MLflow does not orchestrate the distributed training itself -- that remains the job of the training framework and cluster manager.

### Q7: How do I handle experiment cleanup and storage costs?

Use `mlflow gc` to garbage-collect deleted runs and reclaim artifact storage. Set retention policies at the experiment level. For S3/GCS artifact stores, configure lifecycle rules to transition old artifacts to cheaper storage tiers. Monitor backend database size and vacuum regularly. For large-scale cleanup, use the MlflowClient API to programmatically delete runs matching specific criteria (age, tags, metrics below threshold).

### Q8: How do I secure a production MLflow deployment?

MLflow's open-source version does not include built-in authentication. For production: (1) deploy behind a reverse proxy with OAuth2/OIDC authentication, (2) use the artifact proxy mode to avoid distributing object store credentials, (3) restrict network access to the tracking server, (4) encrypt data in transit (TLS) and at rest (S3 server-side encryption). Databricks Managed MLflow provides built-in access control, audit logging, and workspace isolation.

### Q9: What are the gotchas when migrating from MLflow 2.x to 3.x?

Key changes in MLflow 3.x: the `LoggedModel` entity is now a first-class citizen (models are tracked independently of runs), model stages are deprecated in favor of aliases, and the tracing API has been significantly expanded. Most 2.x tracking code works without changes. The main migration tasks are: replacing stage-based workflows with alias-based ones, updating any code that relies on the old Model Registry stage transitions, and adopting the new tracing APIs for GenAI workloads.

### Q10: How do I evaluate LLM outputs systematically?

Use `mlflow.evaluate()` with LLM judges. MLflow provides 50+ built-in metrics and judges that assess answer relevance, faithfulness, toxicity, and more. You can also define custom judges. Evaluations can be run from code or directly from the Traces UI (no-code evaluation). For production monitoring, configure continuous evaluation with LLM judges that automatically score new traces as they arrive.
