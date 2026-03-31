## Trade-offs & Limitations
<!-- level: intermediate -->
<!-- references:
- [MLflow vs Weights & Biases vs ZenML](https://www.zenml.io/blog/mlflow-vs-weights-and-biases) | blog
- [Kubeflow vs MLflow](https://ubuntu.com/blog/kubeflow-vs-mlflow) | blog
- [MLOps Tools Comparison](https://kanerika.com/blogs/mlops-tool/) | blog
- [A Brief Comparison of Kubeflow vs MLflow](https://jfrog.com/blog/a-brief-comparison-of-kubeflow-vs-mlflow/) | blog
-->

### Strengths

- **Open source and vendor-neutral:** Apache 2.0 license with Linux Foundation governance. No lock-in to any cloud provider. You own your data and infrastructure.
- **Low barrier to entry:** `pip install mlflow` and `mlflow.autolog()` gets you experiment tracking in minutes. No infrastructure required to start.
- **Framework agnostic:** Works with any ML library. The model flavor system abstracts away framework differences for deployment.
- **Massive community:** 800+ contributors, 18k+ GitHub stars, 25M+ monthly downloads. Extensive third-party integrations and community support.
- **Full lifecycle coverage:** Tracking, model packaging, registry, serving, and (with 3.x) GenAI observability in a single platform.
- **GenAI-native (3.x):** First-class tracing, LLM evaluation, and AI Gateway support. Not a bolted-on afterthought.

### Limitations

- **No built-in authentication:** The open-source server has no access control. Production deployments require a reverse proxy with external auth, which adds operational complexity.
- **Not a pipeline orchestrator:** MLflow tracks experiments but doesn't schedule or orchestrate training pipelines. You need a separate tool (Airflow, Prefect, Kubeflow) for DAG-based workflows.
- **UI performance at scale:** The tracking UI can become slow with thousands of runs if using the file-based backend. Even with a database, the UI's search and comparison features have limits at very high run counts.
- **Single-writer artifact limitation:** Concurrent artifact writes from multiple processes can cause conflicts, especially with file-based stores. Remote stores (S3, GCS) handle this better.
- **Limited real-time monitoring:** MLflow is designed for experiment logging, not real-time model monitoring. For data drift detection, prediction monitoring, and alerting, pair it with tools like Evidently, WhyLabs, or Arize.

### MLflow vs. Weights & Biases (W&B)

| Aspect | MLflow | W&B |
|--------|--------|-----|
| License | Open source (Apache 2.0) | Proprietary (free tier available) |
| Hosting | Self-hosted or Databricks managed | SaaS-first (self-hosted available) |
| Experiment tracking UI | Functional but basic | Rich, polished, collaborative |
| Visualization | Standard charts, metric comparison | Advanced visualizations, custom panels, reports |
| Pipeline orchestration | No | W&B Launch (limited) |
| Model registry | Full-featured with aliases | Artifact versioning, less governance-focused |
| GenAI/LLM support | Extensive (tracing, eval, gateway) | W&B Weave for tracing and eval |
| Cost | Free (infra costs) | Free tier; $50-200/user/month for teams |
| Data ownership | Full (your infrastructure) | Stored on W&B servers (or self-hosted) |

**Choose MLflow when:** data sovereignty matters, you need full model lifecycle governance, you want vendor neutrality, or you're in a Databricks ecosystem.

**Choose W&B when:** you want best-in-class visualization and collaboration UX, your team is small-to-medium, and you prefer SaaS simplicity over infrastructure management.

### MLflow vs. DVC

| Aspect | MLflow | DVC |
|--------|--------|-----|
| Primary focus | Full ML lifecycle | Data and model versioning (Git-based) |
| Experiment tracking | Built-in with UI | Via DVCLive (lighter-weight) |
| Data versioning | Limited (artifacts) | Core strength (Git-like for data) |
| Pipeline orchestration | No | DVC Pipelines (DAG-based, declarative) |
| Model registry | Full-featured | DVC Model Registry (simpler) |
| Learning curve | Moderate | Gentle (Git-familiar concepts) |

**Choose MLflow when:** you need full experiment tracking, model serving, and registry governance.

**Choose DVC when:** data versioning is your primary concern and you want Git-native workflows.

### MLflow vs. Kubeflow

| Aspect | MLflow | Kubeflow |
|--------|--------|----------|
| Primary focus | Experiment tracking + model management | Pipeline orchestration + training at scale |
| Infrastructure | Lightweight (Python process) | Kubernetes-native (heavy infrastructure) |
| Pipeline orchestration | No | Core strength (Kubeflow Pipelines) |
| Distributed training | Tracks results, doesn't orchestrate | Manages distributed training (PyTorchJob, etc.) |
| Model serving | Basic built-in, integrates with others | KServe (production-grade serving) |
| Complexity | Low | High (requires Kubernetes expertise) |
| Setup time | Minutes | Days to weeks |

**Choose MLflow when:** you need experiment tracking and model management without heavy infrastructure overhead.

**Choose Kubeflow when:** you need Kubernetes-native pipeline orchestration and distributed training management. Many teams use both -- Kubeflow for orchestration, MLflow for tracking and registry.

### The Pragmatic Recommendation

MLflow is the best starting point for most ML teams. Its low barrier to entry, vendor neutrality, and full lifecycle coverage make it a safe foundational choice. As teams scale, they typically layer complementary tools on top -- a pipeline orchestrator for workflow management, a feature store for feature engineering, and a monitoring tool for production observability -- rather than replacing MLflow.
