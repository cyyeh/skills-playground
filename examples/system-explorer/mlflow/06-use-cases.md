## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
<!-- references:
- [MLflow Use Cases](https://mlflow.org/docs/latest/) | official-docs
- [MLflow in 2025: The New Backbone of Enterprise MLOps](https://www.sparity.com/blogs/mlflow-3-0-enterprise-mlops/) | blog
- [A Comprehensive Guide to MLflow for Data Scientists](https://medium.com/@elmahfoudradwane/a-comprehensive-guide-to-mlflow-for-data-scientists-real-world-applications-and-examples-d4a2a32dda22) | blog
-->

### When to Use It

**Experiment tracking for ML teams of any size.** If your team is running more than a handful of experiments per week and tracking results in spreadsheets, shared notebooks, or (worst) not at all, MLflow immediately pays for itself. The tracking overhead is minimal (a few lines of code) and the return is huge: you can search, compare, and reproduce any experiment months later. This is MLflow's original and strongest use case.

**Model packaging and deployment standardization.** When you need to deploy models across diverse environments (REST endpoints, batch Spark jobs, edge devices via ONNX) and want a single packaging format that works everywhere. The pyfunc flavor system means your deployment pipeline does not need to know whether the model was trained with scikit-learn, PyTorch, or a custom framework. Organizations with 5+ models in production benefit most from this standardization.

**Model lifecycle governance.** When your organization needs to track which model version is deployed where, who approved it, and what training data produced it. Regulated industries (finance, healthcare, insurance) that require audit trails for model decisions find the model registry indispensable. The alias system (`@champion`, `@challenger`) provides controlled promotion workflows without requiring complex CI/CD pipelines.

**LLM and GenAI application observability.** When building applications with LLMs (chatbots, RAG systems, AI agents), MLflow Tracing provides request-level visibility into every step of the pipeline. If your team is debugging quality issues in a multi-step agent and asking "why did it give the wrong answer to that user?" -- tracing is the tool that shows you exactly which retrieval step, prompt, or tool call went wrong.

**Hyperparameter optimization with tracking.** When running systematic hyperparameter searches (grid search, random search, Bayesian optimization), MLflow captures every trial as a run. Combined with the comparison UI and metric charts, this lets you visualize the hyperparameter landscape and identify the best configuration. Nested runs support multi-level searches (outer loop over architectures, inner loop over hyperparameters).

### When NOT to Use It

**As a data versioning or pipeline orchestration tool.** MLflow tracks experiments and models, not data lineage or pipeline DAGs. If your primary need is versioning training datasets, use [DVC](https://dvc.org/) or [LakeFS](https://lakefs.io/). If you need pipeline orchestration (scheduling, dependency management, retry logic), use [Airflow](https://airflow.apache.org/), [Prefect](https://www.prefect.io/), or [Dagster](https://dagster.io/). MLflow complements these tools; it does not replace them.

**For real-time feature serving.** MLflow does not include a feature store. If you need online feature serving with low-latency lookups, use [Feast](https://feast.dev/), [Tecton](https://www.tecton.ai/), or a cloud-native feature store. MLflow can log which features were used in a run, but it does not manage feature computation or serving.

**As a standalone model serving platform for high-traffic production.** While MLflow can serve models via `mlflow models serve`, this is a lightweight Flask/FastAPI server intended for testing and low-traffic scenarios. For production serving at scale with auto-scaling, A/B testing, canary deployments, and GPU acceleration, use dedicated serving platforms like [Seldon Core](https://www.seldon.io/solutions/open-source-projects/core), [KServe](https://kserve.github.io/website/), [BentoML](https://www.bentoml.com/), [Ray Serve](https://docs.ray.io/en/latest/serve/index.html), or the managed Databricks Model Serving. MLflow model packaging integrates well with all of these.

**When you need sub-millisecond logging overhead.** If your training loop runs at microsecond granularity and logging overhead matters, MLflow's per-call REST round-trips (even with async logging) may introduce unacceptable latency. In these cases, consider buffering metrics locally and logging in bulk at epoch boundaries, or using lighter-weight tracking that logs to local files and syncs later.

**For non-ML software development tracking.** MLflow is purpose-built for ML experiments with concepts like metrics, parameters, and model artifacts. Using it to track general software build performance or non-ML workloads is forcing a square peg into a round hole. Use standard observability tools (Prometheus, Grafana, Datadog) for non-ML metrics.

### Real-World Examples

**FactSet -- Standardized LLMOps for financial services.** [FactSet](https://www.factset.com/), a major financial data provider, implemented MLflow (via Databricks Mosaic AI) to standardize their GenAI development across teams. Before MLflow, their GenAI projects used inconsistent tooling and tracking, making it impossible to compare approaches or reproduce results. After adopting MLflow with tracing and evaluation, they achieved a 70% reduction in code generation latency and 60% reduction in end-to-end latency for text-to-formula generation. The model registry provided the governance required by financial regulators for model approval workflows.

**Enterprise customer churn prediction pipeline.** A published MLOps case study describes using MLflow with Azure DevOps for a production customer churn prediction system. The pipeline uses MLflow experiment tracking to log every retraining run, the model registry to manage version promotion with approval gates, and automated model evaluation that compares new model versions against the current champion before promotion. The result is a fully traceable pipeline where auditors can trace any prediction back to the exact training data, hyperparameters, and code version that produced it.

**Databricks customers at scale.** As the company behind MLflow, Databricks runs it at massive scale for thousands of enterprise customers. MLflow on Databricks manages model registries with hundreds of registered models, experiment histories spanning millions of runs, and real-time tracing of production GenAI applications. This deployment validates MLflow's architecture at enterprise scale, though it is worth noting that the managed Databricks experience includes optimizations and features (Unity Catalog integration, managed endpoints) not available in the open-source version.

**Research teams and academic institutions.** MLflow has been widely adopted in academic ML research for its low barrier to entry. A single researcher can install MLflow with `pip install mlflow`, track experiments locally, and share results by committing the `mlruns` directory to a shared drive or git. When the team grows, they can migrate to a shared tracking server without changing their experiment code. This "start local, scale later" capability is a major adoption driver in research settings.
