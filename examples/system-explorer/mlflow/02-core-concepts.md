## Core Concepts
<!-- level: beginner -->
<!-- references:
- [MLflow Concepts](https://mlflow.org/docs/latest/tracking/) | docs
- [MLflow Models](https://mlflow.org/docs/latest/models.html) | docs
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry/) | docs
-->

### Experiments

**Definition:** An experiment is a named grouping of runs that correspond to a specific task or project -- for example, "fraud-detection-v2" or "image-classifier-resnet."

**Analogy:** Think of an experiment as a folder on your desk labeled with a project name. Every time you try a different approach, you drop a new sheet of results into that folder.

**Why it matters:** Without experiments, runs scatter across an unnamed default bucket. Experiments let teams organize work by project, compare results within a domain, and keep the tracking server navigable as usage grows.

### Runs

**Definition:** A run is a single execution of ML training code. Each run captures parameters (inputs), metrics (outputs), tags (metadata), artifacts (files), and the source code or Git commit that produced it.

**Analogy:** A run is one entry in your lab notebook -- the specific recipe you tried, the measurements you took, and the sample you produced.

**Why it matters:** Runs are the atomic unit of reproducibility. By logging everything about a single execution, you can always go back and understand what happened, why a metric changed, or which hyperparameters produced the best result.

### Tracking

**Definition:** MLflow Tracking is the logging API and UI for recording and querying runs. You call functions like `mlflow.log_param()`, `mlflow.log_metric()`, and `mlflow.log_artifact()` from your training code, and everything gets written to a backend store.

**Analogy:** Tracking is the lab notebook itself -- the system that captures every experiment's details as they happen, and the index that lets you find them later.

**Why it matters:** Tracking is the foundation of MLflow. Without it, experiment results live in scattered CSVs, terminal output, and team Slack messages. With tracking, every result is centralized, searchable, and comparable.

### Model Registry

**Definition:** The Model Registry is a centralized store for managing the full lifecycle of MLflow Models. It provides model versioning, aliasing (e.g., "champion", "challenger"), tagging, annotations, and lineage back to the experiment and run that produced each version.

**Analogy:** The Model Registry is the trophy case for your models. Every model that makes it past experimentation gets a version number, a label, and a place where the team can inspect, compare, and approve it before it goes to production.

**Why it matters:** In production ML, you need to know exactly which model is serving traffic, who trained it, what data it was trained on, and how to roll back. The registry provides this governance layer.

### MLflow Projects

**Definition:** An MLflow Project is a convention for packaging ML code into reusable, reproducible units. An `MLproject` file defines entry points, parameters, and the environment (Conda, Docker, or system) needed to run the code.

**Analogy:** A project is a recipe card that lists not just the ingredients (parameters) and steps (code), but also the kitchen (environment) needed to cook the dish.

**Why it matters:** Projects solve the "it worked on my machine" problem. Anyone can run `mlflow run <project-uri>` and get the same environment and execution, whether on a laptop, a CI server, or a cloud cluster.

### Artifacts

**Definition:** Artifacts are output files associated with a run -- model weights, plots, serialized data, evaluation reports, or any other file. They are stored in an artifact store (local filesystem, S3, Azure Blob, GCS, etc.).

**Analogy:** Artifacts are the physical samples and photos from your lab work -- not the numbers in the notebook, but the tangible outputs you can pick up and use.

**Why it matters:** Metrics tell you how good a model is, but artifacts give you the actual model. The artifact store ensures every version of every model is preserved and retrievable.

### Model Flavors

**Definition:** A model flavor is a standard packaging format that describes how to load and serve a model. MLflow defines native flavors for frameworks like `sklearn`, `pytorch`, `tensorflow`, `xgboost`, `spark`, `langchain`, and many more. The universal `pyfunc` flavor lets any MLflow model be loaded as a generic Python function.

**Analogy:** Flavors are like universal power adapters. Your model was trained with PyTorch (a Japanese plug), but the `pyfunc` flavor lets it plug into any MLflow-compatible socket -- a REST API, a Spark job, or a Kubernetes deployment.

**Why it matters:** Without flavors, deploying a model means writing custom loading and serving code for every framework. Flavors abstract this away, enabling a single deployment pipeline for all your models.

### Recipes (Pipelines)

**Definition:** MLflow Recipes (formerly MLflow Pipelines) provide opinionated, production-ready templates for common ML workflows like classification and regression. They define a step-by-step pipeline from data ingestion through training, evaluation, and registration.

**Analogy:** If MLflow Projects are recipe cards, Recipes are the full meal-prep kits -- pre-portioned ingredients, step-by-step instructions, and quality-check steps built in.

**Why it matters:** Recipes reduce boilerplate and enforce best practices for teams that want a structured, repeatable ML workflow without building a pipeline framework from scratch.

### How They Fit Together

An **experiment** groups related **runs**. Each run uses the **tracking** API to log parameters, metrics, and **artifacts** (including models saved in specific **flavors**). Promising models graduate to the **model registry**, where they are versioned, aliased, and governed. **Projects** ensure that the code behind any run can be reproduced in a consistent environment. **Recipes** provide turnkey templates that orchestrate all of the above into a production-ready pipeline. Together, these concepts form a complete lifecycle: experiment, track, package, register, deploy, and monitor.
