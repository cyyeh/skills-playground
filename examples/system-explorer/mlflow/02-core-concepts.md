## Core Concepts
<!-- level: beginner -->
<!-- references:
- [MLflow Tracking Documentation](https://mlflow.org/docs/latest/ml/tracking/) | official-docs
- [MLflow Models Documentation](https://mlflow.org/docs/latest/ml/model/) | official-docs
- [MLflow Model Registry](https://mlflow.org/docs/latest/ml/model-registry/) | official-docs
- [MLflow Tracing Documentation](https://mlflow.org/docs/latest/genai/tracing/) | official-docs
-->

### Experiment

An **Experiment** is a named container that groups related runs together -- like a folder in a filing cabinet labeled "Customer Churn Models" or "Image Classifier v2." When you are working on a specific ML task, you create an experiment to hold all the different attempts (runs) you make at solving it. Experiments keep your work organized so you can compare results within a single task without wading through unrelated models. Each experiment has a unique ID and a configurable artifact storage location for its runs' outputs.

### Run

A **Run** is a single execution of your ML training code -- like one entry in a lab notebook recording a specific experiment attempt. Each run captures everything about that particular execution: the hyperparameters you chose (parameters), the performance numbers you measured (metrics), the output files produced (artifacts), and any labels you attach (tags). Runs are the fundamental unit of tracking in MLflow. You can start a run, log data throughout its execution, and end it with a status (finished, failed, or killed). Runs can be nested, allowing you to represent parent-child relationships like a hyperparameter search containing multiple training iterations.

### Parameter

A **Parameter** is a key-value pair representing an input configuration to your run -- like the settings on a camera before taking a photo. Parameters are typically hyperparameters (learning rate, batch size, number of layers) but can be any string value that describes how the run was configured. Once logged, parameters are immutable for that run. They are stored in the [backend store](https://mlflow.org/docs/latest/self-hosting/architecture/backend-store/) alongside other metadata and are searchable across runs, making it easy to filter for runs with specific configurations.

### Metric

A **Metric** is a numerical measurement recorded during or after a run -- like the score on a test that tells you how well your model performed. Metrics have a key (name), a numeric value, a timestamp, and an optional step number. Unlike parameters, metrics can be logged multiple times per run at different steps, creating a history that you can visualize as a curve (e.g., loss decreasing over training epochs). MLflow supports linking metrics to specific model checkpoints and datasets, enabling fine-grained performance tracking. Common examples include accuracy, loss, F1 score, and latency.

### Artifact

An **Artifact** is any output file produced by a run -- like the physical deliverables from a manufacturing process. Artifacts can be model weight files, images, data files, serialized objects, or any binary content. They are stored in the [artifact store](https://mlflow.org/docs/latest/self-hosting/architecture/overview/) (local filesystem, S3, Azure Blob Storage, GCS) separately from the metadata because they are often large. You can log individual files or entire directories. The most important artifact for most runs is the model itself, which MLflow packages in a standardized format.

### Model (MLflow Model)

An **MLflow Model** is a standardized packaging format for ML models -- like a shipping container that ensures your cargo (the trained model) can be transported and unloaded anywhere regardless of how it was built. An MLflow Model is a directory containing the serialized model, an `MLmodel` YAML descriptor, dependency specifications (`conda.yaml`, `requirements.txt`), and optionally an input example and signature. The key innovation is the [flavor system](https://mlflow.org/docs/latest/ml/model/): each model can declare multiple "flavors" (e.g., `sklearn`, `python_function`) that tell deployment tools how to load and serve it. This decouples the training framework from the serving infrastructure.

### Flavor

A **Flavor** is a convention that defines how a model from a specific framework should be saved, loaded, and served -- like an adapter that lets different plugs fit the same socket. For example, a scikit-learn model has both an `sklearn` flavor (loadable as a native sklearn object) and a `python_function` flavor (loadable as a generic Python callable). The `python_function` (pyfunc) flavor acts as a universal interface: any model that supports it can be served through the same REST endpoint, loaded as a Spark UDF, or deployed to any MLflow-compatible platform. MLflow ships with built-in flavors for scikit-learn, PyTorch, TensorFlow, XGBoost, LightGBM, Hugging Face Transformers, ONNX, Spark MLlib, and many more.

### Model Registry

The **Model Registry** is a centralized store for managing model versions and their lifecycle -- like a library catalog that tracks every edition of every book, who checked it out, and whether it is recommended for readers. Registered models have a name, an auto-incrementing version number with each new registration, aliases (mutable pointers like `@champion` or `@challenger`), tags, and markdown annotations. The registry links each model version back to the run that produced it, providing full lineage. Teams use the registry to promote models through stages (development to staging to production) with governance controls.

### Trace

A **Trace** captures the full execution path of a GenAI request through your application -- like an X-ray that shows every bone and organ a signal passes through. Each trace consists of spans representing individual steps (LLM calls, tool invocations, retrieval operations) arranged in a tree structure. Traces record inputs, outputs, latency, token usage, and metadata at each step. MLflow Tracing is fully [OpenTelemetry-compatible](https://opentelemetry.io/) and supports auto-tracing for frameworks like OpenAI, Anthropic, LangChain, and LlamaIndex with a single line of code. Traces are essential for debugging agent behavior and monitoring production GenAI applications.

### How They Fit Together

The concepts form a layered workflow. You create an **Experiment** to organize your work on a task. Within that experiment, each training attempt is a **Run** that logs **Parameters** (inputs), **Metrics** (measurements), and **Artifacts** (outputs). The most important artifact is usually an MLflow **Model**, packaged with one or more **Flavors** that define how it can be loaded. When a model is ready for team review, you register it in the **Model Registry**, which tracks versions and lifecycle state. For GenAI applications, **Traces** provide observability into how your LLM-powered application processes each request, complementing the experiment-level tracking with request-level visibility. Together, these concepts cover the full lifecycle: experimentation (Runs, Parameters, Metrics), packaging (Models, Flavors), governance (Registry), and production observability (Traces).
