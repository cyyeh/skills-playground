## Ecosystem & Integrations
<!-- level: intermediate -->
<!-- references:
- [MLflow Plugins Documentation](https://mlflow.org/docs/latest/plugins.html) | official-docs
- [MLflow Integrations](https://mlflow.org/docs/latest/ml/traditional-ml/tutorials/) | official-docs
- [MLflow GenAI Integrations](https://mlflow.org/genai) | official-docs
- [MLflow Community Plugins](https://github.com/mlflow/mlflow/blob/master/README.md) | github
-->

### Official Tools & Extensions

**MLflow Tracking UI** -- A built-in web interface for exploring experiments, comparing runs, visualizing metrics, managing the model registry, and viewing traces. Served directly by the tracking server. Provides metric comparison charts, parameter search, artifact browsers, and trace detail views. The UI has been significantly enhanced in MLflow 3.x with GenAI-specific dashboards for agent performance monitoring.

**MLflow CLI** -- A comprehensive command-line tool for common operations: `mlflow server` (start tracking server), `mlflow models serve` (deploy a model as a REST endpoint), `mlflow models predict` (batch inference), `mlflow db upgrade` (database migration), `mlflow artifacts` (artifact management), and `mlflow deployments` (model deployment management). The CLI provides scriptable access to most MLflow operations for use in CI/CD pipelines.

**MLflow AI Gateway** -- A centralized proxy for managing LLM API endpoints with a YAML configuration file. The gateway provides rate limiting, API key management, and hot-swappable endpoint configuration without server restarts. It unifies access to multiple LLM providers (OpenAI, Anthropic, Azure OpenAI, custom endpoints) behind a consistent interface.

**mlflow-skinny** -- A lightweight installation of MLflow that includes only tracking and evaluation dependencies, excluding ML framework integrations. Useful for environments where you need to log metrics and parameters but do not need model packaging or serving. Approximately 90% smaller than the full installation.

**mlflow-tracing** -- An ultra-lightweight package (95% smaller than full MLflow) designed for production GenAI applications that only need tracing capabilities. It provides the full tracing API with async export and minimal memory footprint, making it suitable for latency-sensitive production deployments.

**MLflow Go Backend** -- An experimental [Go-based backend implementation](https://github.com/mlflow/mlflow-go-backend) (`mlflow-go-backend` package) that can replace the Python tracking server for higher throughput. It implements the same REST API as the Python server but with better concurrent request handling and lower memory usage. Installable as a Python package that plugs into the standard MLflow server.

### Community Ecosystem

**ML Framework Auto-Logging Integrations** -- MLflow provides built-in auto-logging for major ML frameworks: [scikit-learn](https://scikit-learn.org/), [XGBoost](https://xgboost.readthedocs.io/), [LightGBM](https://lightgbm.readthedocs.io/), [PyTorch](https://pytorch.org/), [TensorFlow](https://www.tensorflow.org/)/Keras, [Spark MLlib](https://spark.apache.org/mllib/), [statsmodels](https://www.statsmodels.org/), [fastai](https://docs.fast.ai/), [PaddlePaddle](https://www.paddlepaddle.org.cn/), and [Prophet](https://facebook.github.io/prophet/). Each integration automatically captures framework-specific parameters, metrics, and models during training.

**GenAI Framework Auto-Tracing** -- One-line auto-tracing integrations for [OpenAI](https://platform.openai.com/docs/), [Anthropic](https://docs.anthropic.com/), [LangChain](https://www.langchain.com/), [LlamaIndex](https://www.llamaindex.ai/), [DSPy](https://dspy-docs.vercel.app/), [Vercel AI SDK](https://sdk.vercel.ai/docs/introduction), [AutoGen](https://microsoft.github.io/autogen/), and [Haystack](https://haystack.deepset.ai/). These integrations instrument the framework's LLM calls, tool invocations, and retrieval operations to produce detailed traces.

**Hugging Face Transformers Integration** -- Deep integration with [Hugging Face](https://huggingface.co/) for logging and deploying transformer models. Supports logging models with the `transformers` flavor, including tokenizers, model configs, and pipeline objects. Models can be loaded from the Hugging Face Hub and wrapped as MLflow models.

**ONNX Support** -- The `onnx` flavor enables cross-framework model interoperability. Models converted to [ONNX format](https://onnx.ai/) can be logged, versioned, and deployed through MLflow, enabling scenarios where models are trained in Python but served in C++, JavaScript, or mobile runtimes.

**Plugin System** -- MLflow's plugin architecture allows custom tracking store backends, artifact stores, and deployment targets to be registered via Python entry points. Community plugins include integrations with [Aliyun OSS](https://www.alibabacloud.com/product/object-storage-service) for artifact storage, [Google Cloud Storage](https://cloud.google.com/storage) backends, and custom authentication plugins for the tracking server.

### Common Integration Patterns

**MLflow + Cloud ML Platforms.** MLflow integrates natively with [Databricks](https://www.databricks.com/product/managed-mlflow) (managed MLflow with Unity Catalog), [Amazon SageMaker](https://docs.aws.amazon.com/sagemaker/latest/dg/mlflow.html) (managed MLflow on SageMaker AI), and [Azure Machine Learning](https://learn.microsoft.com/en-us/azure/machine-learning/) (MLflow as a native tracking backend). These integrations provide managed infrastructure, enterprise authentication, and platform-specific optimizations while maintaining the standard MLflow API.

**MLflow + Kubernetes Serving.** The standard pattern for production model serving combines MLflow model packaging with Kubernetes-native serving frameworks. Package your model as an MLflow model, build a Docker container using `mlflow models build-docker`, and deploy to [KServe](https://kserve.github.io/website/) or [Seldon Core](https://www.seldon.io/solutions/open-source-projects/core). The pyfunc interface provides the consistent prediction API that these frameworks require.

**MLflow + Pipeline Orchestrators.** Use [Airflow](https://airflow.apache.org/), [Prefect](https://www.prefect.io/), or [Dagster](https://dagster.io/) for orchestrating training pipelines, with MLflow handling experiment tracking and model management within each pipeline task. Each training task creates an MLflow run, logs metrics and artifacts, and optionally registers the model. The orchestrator handles scheduling, dependencies, and retries.

**MLflow + Feature Stores.** Combine MLflow with [Feast](https://feast.dev/) or a cloud-native feature store. The feature store manages feature computation and serving; MLflow logs which feature set version was used during training (via `mlflow.log_input()`) and tracks the resulting model. This creates full lineage from features to model version.

**MLflow + Experiment-Level Orchestration.** For hyperparameter optimization, combine MLflow tracking with [Optuna](https://optuna.org/), [Ray Tune](https://docs.ray.io/en/latest/tune/index.html), or [Hyperopt](http://hyperopt.github.io/hyperopt/). The optimizer suggests hyperparameter configurations; each trial is logged as an MLflow run. MLflow's search and comparison features then help analyze the optimization landscape and select the best configuration.

**MLflow + CI/CD Systems.** Integrate MLflow into CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins) for automated model training, evaluation, and deployment. The pipeline triggers retraining on data or code changes, logs results to MLflow, compares against the current champion model in the registry, and promotes the new version if it passes evaluation criteria. The model registry's alias system provides the promotion mechanism without custom scripting.
