## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
<!-- references:
- [MLflow Use Cases](https://mlflow.org) | official-docs
- [Databricks Managed MLflow](https://www.databricks.com/product/managed-mlflow) | official-docs
- [MLflow Real-World Applications](https://medium.com/@elmahfoudradwane/a-comprehensive-guide-to-mlflow-for-data-scientists-real-world-applications-and-examples-d4a2a32dda22) | blog
- [LLMOps Case Studies](https://www.zenml.io/blog/llmops-in-production-457-case-studies-of-what-actually-works) | blog
-->

### When to Use MLflow

**Experiment tracking for ML teams:** Any team running more than a handful of training experiments benefits from MLflow Tracking. It replaces spreadsheets, scattered notebooks, and tribal knowledge with a searchable, versioned experiment store. Even a solo data scientist gains value from being able to compare last week's runs against today's.

**Model lifecycle management:** When models move from research to production, the Model Registry provides the governance layer: versioning, alias management (@champion/@challenger), lineage tracking, and promotion workflows. This is critical for regulated industries (finance, healthcare) where audit trails are mandatory.

**GenAI application observability:** With MLflow 3.x, the platform provides first-class tracing for LLM-based applications. Teams building agents, RAG pipelines, or chatbots use MLflow to debug non-deterministic behavior, track token costs, and evaluate output quality at scale.

**Multi-framework, multi-cloud environments:** Organizations using a mix of PyTorch, TensorFlow, scikit-learn, and XGBoost across AWS, Azure, and on-premises infrastructure benefit from MLflow's framework-agnostic model format and pluggable artifact stores.

### When NOT to Use MLflow

**Heavy pipeline orchestration:** MLflow is not a workflow scheduler. If you need DAG-based pipeline orchestration with retries, scheduling, and dependency management, use Airflow, Prefect, Kubeflow Pipelines, or Dagster alongside MLflow.

**Large-scale distributed training:** MLflow tracks experiments but does not manage distributed compute. For distributed training across GPU clusters, use frameworks like Horovod, DeepSpeed, or Ray Train, and log results to MLflow.

**Real-time feature serving:** MLflow does not include a feature store. For real-time feature computation and serving, pair it with Feast, Tecton, or a cloud-native feature store.

### Real-World Deployments

**FactSet (Financial Analytics):** Implemented MLflow within a Databricks-based LLMOps framework to standardize GenAI development across teams. Achieved 70% reduction in latency for code generation and 60% reduction in end-to-end latency for text-to-formula generation by using MLflow to track experiments and manage model versions across fine-tuned open-source models.

**Enterprise Churn Prediction Pipeline:** A documented case study shows MLflow orchestrated with Azure DevOps and Databricks Asset Bundles for a self-healing, production-grade churn prediction pipeline. MLflow captured every parameter, metric, and artifact with enterprise-grade fidelity, while Azure DevOps enforced quality gates. The result was a fully traceable, reproducible pipeline that autonomously retrains, validates, and promotes models.

**Large-Scale Recommendation Systems:** Teams at major tech companies use MLflow to manage thousands of daily experiment runs for recommendation models. The platform's ability to compare metrics across runs at scale, combined with the Model Registry's promotion workflows, enables rapid iteration with production safety.

**GenAI Agent Development:** Organizations building customer-facing chatbots and AI agents use MLflow Tracing to monitor production conversations, evaluate response quality with LLM judges, and track token costs across multiple LLM providers via the AI Gateway. The trace-to-experiment linkage enables root-cause analysis when agent quality degrades.

**Healthcare ML Compliance:** Healthcare organizations leverage the Model Registry's lineage tracking and versioning to maintain FDA-compliant audit trails. Every model in production can be traced back to its exact training data, code version, hyperparameters, and validation metrics.
