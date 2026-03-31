## Common Q&A
<!-- level: all -->
<!-- references:
- [MLflow Documentation](https://mlflow.org/docs/latest/) | docs
- [MLflow GitHub Issues](https://github.com/mlflow/mlflow/issues) | github
-->

### Q1: What is the difference between MLflow and Databricks?

**A:** MLflow is the open-source project (Apache-2.0 licensed) that anyone can run anywhere. Databricks is the company that created MLflow and offers a managed, enterprise version as part of the Databricks Lakehouse Platform. Managed MLflow on Databricks adds features like Unity Catalog integration, auto-scaling model serving, workspace access control, and the AI Gateway -- but the core MLflow functionality is identical to the open-source version. You are never locked into Databricks.

### Q2: Can I use MLflow without a tracking server?

**A:** Yes. By default, MLflow writes to a local `./mlruns` directory -- no server needed. This is fine for individual use. However, for team collaboration, a remote tracking server backed by a database and cloud artifact store is strongly recommended. The tracking server also enables the web UI for visual comparison.

### Q3: How does autologging work, and does it affect my training performance?

**A:** Autologging uses monkey-patching to intercept `.fit()` calls in supported libraries. It logs parameters before training and metrics/artifacts after training completes. The performance overhead is minimal -- typically less than 1% of total training time -- because logging calls are I/O-bound (network requests to the tracking server) and happen at the start/end of training, not during computation-heavy forward/backward passes. If logging fails, the training code continues uninterrupted.

### Q4: What happens when my tracking server goes down during training?

**A:** If the tracking server is unreachable, MLflow client calls will raise exceptions. However, autologging is wrapped in a `safe_patch` that catches exceptions and logs warnings without crashing your training code. For manual logging, you should wrap `mlflow.log_*` calls in try/except blocks in production. Some teams also configure a local fallback store and sync results later.

### Q5: How do I handle large artifacts (multi-GB models)?

**A:** Use a cloud artifact store (S3, Azure Blob, GCS) rather than the tracking server's local filesystem. Enable the artifact proxy (`--serve-artifacts`) on the tracking server so clients upload through the server, or configure direct client-to-store access for higher throughput. For very large models (10GB+), consider using MLflow's support for external artifact URIs that reference pre-existing storage locations.

### Q6: Can I track experiments in Jupyter notebooks?

**A:** Absolutely. MLflow is designed for notebook-first workflows. Add `mlflow.autolog()` at the top of your notebook, and every cell that trains a model will be tracked. You can view runs in the MLflow UI, or query them directly in the notebook using `mlflow.search_runs()` which returns a Pandas DataFrame.

### Q7: How do model aliases work compared to the old stage transitions?

**A:** Before MLflow 2.9, the Model Registry used fixed stages: "Staging", "Production", "Archived." These were replaced by **aliases** -- arbitrary string labels (e.g., "champion", "challenger", "shadow") that you define. Aliases are more flexible: you can have any number of them, they are mutable pointers to specific versions, and they work better with modern CI/CD and A/B testing workflows. To load a model by alias: `mlflow.pyfunc.load_model("models:/my-model@champion")`.

### Q8: Is MLflow suitable for deep learning with long-running training?

**A:** Yes. For deep learning, use `mlflow.log_metric("loss", value, step=epoch)` to log metrics at each epoch, creating time-series plots in the UI. Autologging for PyTorch, TensorFlow, and Keras handles this automatically. For very long runs (hours to days), metrics are persisted incrementally -- you can view partial results before training finishes. Parent/child runs let you organize hyperparameter sweeps where a parent run contains the sweep configuration and child runs contain individual trials.

### Q9: How do I migrate from Weights & Biases (or another tool) to MLflow?

**A:** There is no one-click migration, but the process is straightforward: (1) Export your W&B runs as CSV or JSON. (2) Write a script that reads the exported data and calls `mlflow.log_param()`, `mlflow.log_metric()`, and `mlflow.log_artifact()` for each run. (3) For models, re-log them using the appropriate MLflow flavor. Many teams run both tools in parallel during migration, logging to MLflow and the existing tool simultaneously, then switching over once the team is comfortable.

### Q10: Can MLflow handle multi-tenant or multi-team setups?

**A:** Since MLflow 3.10, the tracking server supports **organizations** -- a multi-workspace feature that lets teams logically isolate experiments, models, and prompts within a single server. For earlier versions, teams typically use separate experiments with naming conventions, or deploy separate tracking server instances. On Databricks, Unity Catalog provides fine-grained access control across workspaces. For open-source deployments, you can add authentication via a reverse proxy (nginx with OIDC) or use MLflow's built-in authentication (available since MLflow 2.5).
