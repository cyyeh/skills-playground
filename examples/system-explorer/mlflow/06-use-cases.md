## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
<!-- references:
- [From Tracking to Deployment: Managing ML Experiments with MLflow](https://www.opensourceforu.com/2026/03/from-tracking-to-deployment-managing-ml-experiments-with-mlflow/) | blog
- [MLflow on Databricks](https://docs.databricks.com/aws/en/mlflow/) | official-docs
- [A Practical Guide to MLflow: From Chaos to Production-Ready ML Workflows](https://medium.com/@omari.james.data/a-practical-guide-to-mlflow-from-chaos-to-production-ready-ml-workflows-3fa37bd95ef9) | blog
-->

### When to Use It

**Experiment tracking and comparison.** You are running dozens or hundreds of training experiments with different hyperparameters, features, or model architectures, and you need to systematically compare results. MLflow's tracking UI lets you visualize learning curves, compare metrics across runs, and filter runs by parameter values. This is MLflow's core sweet spot -- any data scientist who has ever lost track of "which notebook produced the best model" needs this.

**Team-based ML development.** Multiple data scientists work on the same model, each trying different approaches. MLflow provides a shared tracking server where everyone logs their runs, making it easy to see what others have tried, avoid duplicate work, and build on successful approaches. The experiment and run organization prevents the "my-model-final-v3-REAL-final.pkl" chaos.

**Model versioning and promotion.** You need a governed workflow for moving models from development to staging to production. The model registry provides version tracking, alias management, and audit trails. When something goes wrong in production, you can immediately identify which model version is deployed, who promoted it, and from which training run it came.

**Reproducible ML pipelines.** You need to guarantee that a training run can be exactly reproduced -- same code, same data, same environment, same results. MLflow captures parameters, code version (via Git tags), environment specifications (conda.yaml), and dataset references, providing the complete provenance chain.

**Multi-framework model deployment.** Your team uses different ML frameworks (scikit-learn for tabular data, PyTorch for deep learning, XGBoost for gradient boosting) but you want a single deployment pipeline. MLflow's pyfunc flavor unifies all frameworks behind a common `predict()` interface, so one deployment system handles everything.

**LLM and AI agent observability.** You are building LLM applications or AI agents and need to trace request lifecycles, evaluate prompt quality, and monitor production behavior. MLflow's tracing and evaluation capabilities (added in recent versions) extend experiment tracking to generative AI workflows.

### When NOT to Use It

**Real-time feature serving.** MLflow is not a feature store. It tracks experiments and manages models, but it doesn't serve features to production models at inference time. For that, use Feast, Tecton, or a similar feature platform alongside MLflow.

**Distributed model training.** MLflow doesn't parallelize or distribute training across multiple machines. It tracks the results of training, regardless of how training is distributed. Use Horovod, Ray Train, or DeepSpeed for distributed training and log the results to MLflow.

**Data pipeline orchestration.** MLflow is not a workflow orchestrator. It doesn't schedule training jobs, manage dependencies between pipeline steps, or handle retries. Use Airflow, Prefect, Dagster, or Kubeflow Pipelines for orchestration, and have each pipeline step log to MLflow.

**Small, one-off analyses.** If you're running a single Jupyter notebook for a quick analysis that won't be repeated, the overhead of setting up MLflow tracking may not be worth it. MLflow shines when you have multiple runs to compare or models to manage over time.

**Extreme-scale metric logging.** If your training loop logs thousands of metrics per second (e.g., per-batch losses in large-scale distributed training), the MLflow tracking server can become a bottleneck. Consider aggregating metrics before logging (e.g., log per-epoch averages instead of per-batch values) or using a specialized metrics backend.

### Real-World Examples

**Databricks -- Managed MLflow at Scale**
Databricks, the company behind MLflow, operates a managed MLflow service used by thousands of enterprises. Their platform processes billions of logged metrics and manages millions of model versions across industries including finance, healthcare, and retail. The managed service adds enterprise features (access control, audit logging, Unity Catalog integration) on top of the open-source core.

**Manufacturing -- Predictive Maintenance**
A manufacturing company uses MLflow's Model Registry to manage anomaly detection models deployed on production equipment. Different model versions are staged and tested on historical failure data before deployment. The registry's aliasing system lets them instantly roll back to a previous model version if a new deployment shows degraded performance on the factory floor.

**Autonomous Vehicles -- Reproducible Perception Models**
A self-driving car company leverages MLflow to ensure reproducibility of perception and control algorithms. Each model training run is logged with the exact dataset version, code commit, hyperparameters, and environment. When a model exhibits unexpected behavior in road testing, engineers can trace back to the exact training conditions and reproduce the issue.

**Netflix-style Recommendation Systems**
Organizations building recommendation engines use MLflow to manage continuous experimentation. Multiple model variants (collaborative filtering, content-based, hybrid) are tracked as experiments, with the model registry managing A/B test assignments. The champion/challenger alias pattern enables gradual traffic shifting between model versions.

**Financial Services -- Fraud Detection**
Banks use MLflow to maintain audit trails for fraud detection models, which are subject to regulatory compliance requirements. Every model version is linked to its training data, parameters, and performance metrics. The model registry's tagging system captures compliance metadata (reviewer, approval date, risk assessment), creating a governance trail that satisfies regulatory auditors.
