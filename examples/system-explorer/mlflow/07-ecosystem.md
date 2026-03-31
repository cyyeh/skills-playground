## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [MLflow Integrations](https://mlflow.org/docs/latest/ml/) | docs
- [MLflow Plugins](https://mlflow.org/docs/latest/ml/plugins) | docs
- [MLflow GenAI Integrations](https://mlflow.org/genai) | docs
-->

### Framework Integrations

MLflow provides native, first-class integrations with major ML and AI frameworks via dedicated modules:

| Framework | MLflow Module | What's Logged |
|-----------|--------------|---------------|
| scikit-learn | `mlflow.sklearn` | Params, metrics, model, feature importance |
| PyTorch | `mlflow.pytorch` | Params, loss curves, model state dict |
| TensorFlow / Keras | `mlflow.tensorflow` | Params, epoch metrics, SavedModel |
| XGBoost | `mlflow.xgboost` | Params, eval metrics, booster model |
| LightGBM | `mlflow.lightgbm` | Params, metrics, booster model |
| CatBoost | `mlflow.catboost` | Params, metrics, CatBoost model |
| Spark MLlib | `mlflow.spark` | Params, metrics, PipelineModel |
| Statsmodels | `mlflow.statsmodels` | Params, summary stats, model |
| Prophet | `mlflow.prophet` | Params, forecast plots, model |
| spaCy | `mlflow.spacy` | Pipeline config, model |
| ONNX | `mlflow.onnx` | ONNX format model |
| Transformers | `mlflow.transformers` | HuggingFace pipeline, config |

### GenAI and LLM Integrations

Since MLflow 3.0, the platform has extensive GenAI support:

- **OpenAI** (`mlflow.openai`): Autologging for Chat, Completions, and Embeddings API calls.
- **LangChain** (`mlflow.langchain`): Tracing for chains, agents, tools, and retrievers.
- **LlamaIndex** (`mlflow.llama_index`): Tracing for query engines, indices, and retrievers.
- **Anthropic**: Tracing for Claude API calls.
- **Amazon Bedrock**: Tracing for Bedrock model invocations.
- **Google Gemini**: Tracing for Gemini API calls.
- **DSPy**: Tracing for DSPy modules and optimizers.
- **AutoGen / CrewAI**: Tracing for multi-agent frameworks.
- **OpenTelemetry GenAI**: Native support for OTel GenAI Semantic Conventions (since 3.10).

### Cloud Platform Integrations

**Databricks:** MLflow is the native ML platform on Databricks, with managed tracking, model registry, model serving, and the AI Gateway fully integrated. Databricks Unity Catalog extends the model registry with fine-grained access control.

**AWS SageMaker:** MLflow can deploy models directly to SageMaker endpoints using `mlflow.sagemaker.deploy()`. AWS also offers managed MLflow on SageMaker AI.

**Azure ML:** Azure Machine Learning integrates MLflow tracking and model registry natively. Models logged with MLflow can be deployed to Azure managed online endpoints.

**Google Cloud:** MLflow can be deployed on GKE or Cloud Run. Vertex AI supports MLflow tracking for experiment management.

### Deployment Integrations

- **Docker:** Build container images with `mlflow models build-docker`.
- **Kubernetes:** Deploy via Seldon Core, KServe, or custom Kubernetes manifests.
- **Ray Serve:** Community plugin for Ray-based model serving.
- **Databricks Model Serving:** Managed, auto-scaling model endpoints.
- **SageMaker:** Direct deployment to SageMaker endpoints.
- **Azure ML Endpoints:** Deploy to managed online/batch endpoints.

### Data and Feature Store Integrations

- **Delta Lake:** Native integration for reading/writing Delta tables.
- **Feast:** Feature store integration for feature retrieval during training and serving.
- **Unity Catalog:** Databricks governance layer for models, data, and features.

### CI/CD and Orchestration

- **GitHub Actions:** MLflow runs can be triggered from CI pipelines.
- **Apache Airflow:** Airflow operators for triggering MLflow runs and model registration.
- **Prefect / Dagster:** Orchestrators can call MLflow APIs for experiment management.
- **Jenkins:** Standard REST API integration for enterprise CI/CD.

### Community and Governance

- **Linux Foundation project** since 2024, ensuring vendor-neutral governance.
- **900+ contributors** on GitHub.
- **25+ million monthly PyPI downloads.**
- Active community on GitHub Discussions, Slack, and Stack Overflow.
- Regular releases (roughly monthly) with clear changelogs.
- Plugin ecosystem with third-party extensions for custom stores, deployers, and evaluators.

### Package Managers

- **pip:** `pip install mlflow`
- **conda:** `conda install -c conda-forge mlflow`
- **UV:** Supported since MLflow 3.10 with automatic lockfile dependency detection.
- **Docker:** Official images on Docker Hub and GitHub Container Registry.
