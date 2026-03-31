## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [MLflow Integrations](https://mlflow.org) | official-docs
- [MLflow Python API](https://mlflow.org/docs/latest/python_api/index.html) | official-docs
- [MLflow GenAI Integrations](https://mlflow.org/docs/latest/genai/index.html) | official-docs
- [MLflow on Databricks](https://docs.databricks.com/aws/en/mlflow/) | official-docs
-->

### ML Framework Integrations

MLflow provides native autologging for 20+ ML frameworks:

- **Scikit-learn:** Automatic logging of parameters, metrics, and serialized models. The most mature integration.
- **PyTorch / PyTorch Lightning:** Logs training metrics, model checkpoints, and supports the `torch` model flavor.
- **TensorFlow / Keras:** Autologging hooks into `model.fit()` to capture layer configurations, training curves, and saved models.
- **XGBoost / LightGBM / CatBoost:** Parameter and metric autologging with native booster serialization.
- **Spark MLlib:** Pipeline parameter logging and model serialization via the `spark` model flavor.
- **Hugging Face Transformers:** Logs model cards, tokenizer configs, and training arguments. Supports the `transformers` flavor for serving.
- **Statsmodels / Prophet / ARIMA:** Time series model support with parameter and metric logging.

### GenAI / LLM Integrations

MLflow 3.x provides auto-tracing (one-line instrumentation) for:

- **OpenAI** -- Traces chat completions, embeddings, and function calls
- **Anthropic** -- Traces Claude model interactions
- **LangChain / LangGraph** -- Full agent workflow tracing with tool calls
- **LlamaIndex** -- RAG pipeline tracing including retrieval steps
- **DSPy** -- Program optimization traces
- **CrewAI** -- Multi-agent collaboration traces
- **AutoGen** -- Conversational agent traces
- **Google Gemini** -- Chat and embedding traces (Python and TypeScript)
- **AWS Bedrock** -- Model invocation traces
- **Mistral AI** -- Chat completion traces

### Cloud Platform Integrations

- **Databricks (Managed MLflow):** Fully managed tracking server, model registry integrated with Unity Catalog, and serverless model serving. The most feature-complete deployment option.
- **AWS SageMaker:** Deploy MLflow models directly to SageMaker endpoints. MLflow handles container packaging and endpoint configuration.
- **Azure ML:** Native integration for model deployment to Azure ML managed endpoints. Azure Databricks provides managed MLflow.
- **Google Cloud (Vertex AI):** MLflow models can be deployed to Vertex AI endpoints. GCS serves as the artifact store.

### Deployment Targets

- **Docker:** `mlflow models build-docker` creates a self-contained container image for any MLflow model.
- **Kubernetes:** Deploy model containers to K8s clusters via Seldon Core, KServe, or plain deployments.
- **ONNX Runtime:** Convert models to ONNX for optimized inference across hardware targets.
- **Spark:** Load models as Spark UDFs for batch scoring at scale with `mlflow.pyfunc.spark_udf()`.

### Tool Ecosystem

- **MLflow Recipes:** Opinionated ML workflow templates (regression, classification) that encode best practices into predefined pipeline steps.
- **MLflow Evaluate:** Programmatic model evaluation with 50+ built-in metrics and LLM judges for GenAI quality assessment.
- **MLflow Deployments:** Unified deployment API supporting multiple serving platforms from a single interface.

### Language Support

- **Python:** Primary SDK with the richest feature set. All autologging and tracing integrations are Python-native.
- **TypeScript/JavaScript:** MLflow client for Node.js environments. Auto-tracing for OpenAI and Gemini in TypeScript.
- **Java/Scala:** Client library for JVM-based training pipelines and Spark integration.
- **R:** R client for tracking experiments and logging models from R-based workflows.
- **REST API:** Language-agnostic HTTP endpoints for all tracking, registry, and gateway operations.

### Complementary Tools

MLflow is commonly paired with:
- **Airflow / Prefect / Dagster** for pipeline orchestration
- **Feast / Tecton** for feature stores
- **DVC** for data versioning
- **Great Expectations** for data quality validation
- **Prometheus / Grafana** for infrastructure monitoring alongside MLflow's experiment monitoring
