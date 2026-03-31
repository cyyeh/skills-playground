## Overview
<!-- level: beginner -->
<!-- references:
- [MLflow Official Site](https://mlflow.org) | official
- [MLflow GitHub](https://github.com/mlflow/mlflow) | github
- [MLflow Documentation](https://mlflow.org/docs/latest/) | docs
-->

### What Is MLflow?

MLflow is an open-source platform for managing the entire machine learning lifecycle -- from experimentation and training through packaging, deployment, and monitoring. Originally created at Databricks in 2018, it has grown into one of the most widely adopted MLOps tools in the industry, with over 25,000 GitHub stars, 900+ contributors, and 25+ million monthly PyPI downloads as of early 2026.

**One-sentence pitch:** MLflow is the lab notebook, model warehouse, and deployment pipeline for machine learning, all in one open-source toolkit.

### Who Is It For?

- **Data scientists** who want to track experiments without building custom logging infrastructure.
- **ML engineers** who need to package models in a reproducible, framework-agnostic format and deploy them consistently.
- **MLOps teams** managing model registries, governance, and production serving at organizational scale.
- **GenAI developers** who need observability, tracing, and evaluation for LLM-powered applications and agents.

### The Analogy

Think of MLflow as the **version control system for machine learning**. Just as Git tracks every change to your source code, MLflow tracks every experiment you run -- the parameters you used, the metrics you got, the model artifacts you produced. And just as a CI/CD pipeline takes a Git commit and deploys it to production, MLflow takes a registered model version and deploys it to a serving endpoint.

### Why It Matters

Machine learning without experiment tracking is like software development without version control: you end up with unnamed scripts, lost results, and no way to reproduce what worked. MLflow solves the "it worked on my laptop" problem by recording everything needed to reproduce a run and by packaging models in a standard format that works across frameworks and deployment targets.

### Key Differentiators

- **Open source and vendor-neutral:** Apache-2.0 licensed, runs anywhere -- local, cloud, or on-prem.
- **Framework agnostic:** Native integrations for PyTorch, TensorFlow, scikit-learn, XGBoost, Spark MLlib, LangChain, OpenAI, and 100+ other libraries.
- **Unified platform:** Covers tracking, model registry, deployment, and (since MLflow 3.0) GenAI observability with tracing and evaluation.
- **Massive community:** Backed by Databricks, adopted by thousands of organizations worldwide, and supported by a rich plugin ecosystem.
