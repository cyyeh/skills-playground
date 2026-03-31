## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [MLflow Models and Flavors](https://mlflow.org/docs/latest/ml/model/) | official-docs
- [MLflow PyTorch Integration](https://mlflow.org/docs/latest/ml/deep-learning/pytorch/) | official-docs
- [MLflow Official Website](https://mlflow.org) | official-docs
-->

### Official Framework Integrations (Flavors)

**scikit-learn** -- `mlflow.sklearn`. Autologging captures all estimator parameters via `get_params()`, training metrics via `score()`, and serializes models with cloudpickle. Supports pipelines, grid search, and custom transformers.

**PyTorch** -- `mlflow.pytorch`. Logs model architecture, optimizer configuration, training/validation metrics per epoch. Supports both eager and scripted (TorchScript) models. Autologging patches the training loop to capture loss curves automatically.

**TensorFlow / Keras** -- `mlflow.tensorflow` and `mlflow.keras`. Logs model summary, optimizer config, callback metrics, and saves models in SavedModel format. Integrates with TensorBoard for visualization alongside MLflow tracking.

**XGBoost** -- `mlflow.xgboost`. Captures boosting parameters, feature importance, evaluation metrics, and early stopping info. Autologging records eval metrics at each boosting round, creating detailed learning curves.

**LightGBM** -- `mlflow.lightgbm`. Similar to XGBoost integration with parameter logging, feature importance, and per-round metric tracking. Supports both the scikit-learn API and native LightGBM API.

**Spark MLlib** -- `mlflow.spark`. Logs Spark ML pipeline stages, parameters, and metrics. Models are saved in the Spark ML format with a pyfunc wrapper for framework-agnostic serving.

**LangChain** -- `mlflow.langchain`. Traces chain executions, logs prompts and completions, and captures agent tool calls. Autologging patches `invoke()` and `__call__()` to automatically trace LLM interactions.

**OpenAI** -- `mlflow.openai`. Logs API call parameters, token usage, cost tracking, and response content. Integrates with MLflow's tracing system for multi-step LLM workflows.

**Transformers (Hugging Face)** -- `mlflow.transformers`. Logs model configuration, training arguments, and evaluation metrics. Supports text generation, classification, and other pipeline tasks with automatic signature inference.

### Core Tools

**MLflow Tracking UI** -- A React-based web interface for visualizing experiments and runs. Features include metric comparison charts, parallel coordinates plots for hyperparameter analysis, artifact browsing, and run filtering. Accessible via `mlflow ui` or automatically served by the tracking server.

**MLflow CLI** -- Command-line tools for server management, model serving, and project execution:
```bash
mlflow server          # Start tracking server
mlflow models serve    # Serve a model as REST API
mlflow models build-docker  # Build Docker image for a model
mlflow run             # Execute an MLflow Project
```

**MLflow AI Gateway** -- A centralized proxy for managing access to multiple LLM providers (OpenAI, Anthropic, Cohere). Provides rate limiting, cost tracking, API key management, and provider switching without changing application code.

**MLflow Evaluate** -- A framework for evaluating model quality with built-in metrics for classification, regression, and LLM tasks. Supports custom metrics, data slicing, and comparison against baseline models.

### Deployment Integrations

**Docker** -- MLflow builds self-contained Docker images from any model, including dependencies, a serving runtime (Gunicorn/Flask or MLServer), and health check endpoints. Images are Kubernetes-ready.

**Kubernetes** -- Deploy MLflow models as Kubernetes services using the Docker images. Community Helm charts provide tracking server deployment with configurable backends.

**AWS SageMaker** -- `mlflow.sagemaker.deploy()` deploys models directly to SageMaker endpoints with auto-scaling. MLflow handles the container building and endpoint configuration.

**Azure ML** -- Integration with Azure Machine Learning for managed model deployment, monitoring, and auto-scaling.

**Databricks** -- Native integration where Databricks hosts the tracking server, artifact store, and model registry. Unity Catalog provides governance features (access control, lineage, audit logging) on top of the open-source model registry.

### Common Integration Patterns

**MLflow + Airflow/Prefect/Dagster (Orchestration):**
Use your orchestrator to schedule and manage ML pipeline steps. Each step logs to MLflow for tracking. The orchestrator handles "when and in what order to run things"; MLflow handles "what happened and what was produced."

```python
# Airflow DAG task example
def train_model(**context):
    import mlflow
    mlflow.set_tracking_uri("http://mlflow-server:5000")
    with mlflow.start_run():
        # Training code that logs to MLflow
        mlflow.log_params(params)
        model.fit(X_train, y_train)
        mlflow.sklearn.log_model(model, "model")
```

**MLflow + DVC (Data Versioning):**
Use DVC to version datasets and MLflow to track experiments. Log the DVC data hash as an MLflow parameter to link runs to specific dataset versions. This provides full provenance: code (Git) + data (DVC) + experiment (MLflow).

**MLflow + Feature Stores (Feast, Tecton):**
Feature stores provide training and serving features. Log the feature set version and feature names as MLflow parameters. The model registry tracks which model version was trained on which feature set version.

**MLflow + Prometheus/Grafana (Monitoring):**
MLflow tracks training-time metrics. For production monitoring, export model predictions to Prometheus and build Grafana dashboards. Use MLflow's model metadata (expected input schema, training metrics) as baselines for drift detection.

**MLflow + Ray/Optuna (Hyperparameter Tuning):**
Use Ray Tune or Optuna for distributed hyperparameter search. Each trial logs to MLflow as a nested run. The parent run captures the search space and best configuration.

```python
import optuna
import mlflow

def objective(trial):
    lr = trial.suggest_float("lr", 1e-5, 1e-1, log=True)
    with mlflow.start_run(nested=True):
        mlflow.log_param("lr", lr)
        # Train and evaluate
        mlflow.log_metric("accuracy", accuracy)
    return accuracy

with mlflow.start_run(run_name="optuna-search"):
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=100)
```
