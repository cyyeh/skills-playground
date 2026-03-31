## Overview
<!-- level: beginner -->
<!-- references:
- [MLflow Official Website](https://mlflow.org) | official-docs
- [MLflow GitHub Repository](https://github.com/mlflow/mlflow) | github
- [MLflow 3.0 Announcement](https://www.databricks.com/blog/mlflow-30-unified-ai-experimentation-observability-and-governance) | blog
- [MLflow Documentation](https://mlflow.org/docs/latest/) | official-docs
-->

MLflow is an open-source platform for managing the complete machine learning lifecycle, from experiment tracking and reproducible runs to model packaging, versioning, and deployment. Originally created at Databricks in 2018 by Matei Zaharia (co-creator of Apache Spark), MLflow was designed to address the fragmented, ad-hoc nature of ML engineering workflows. It has since become the most widely adopted open-source MLOps platform, with over 800 community contributors, 25+ million monthly PyPI downloads, and adoption by more than 5,000 organizations worldwide. MLflow graduated to a Linux Foundation project, reinforcing its vendor-neutral governance.

The platform is organized around a modular architecture: MLflow Tracking logs experiments (parameters, metrics, artifacts); MLflow Projects packages ML code for reproducibility; MLflow Models provides a standard format for packaging models in multiple "flavors"; and the Model Registry offers centralized model versioning and lifecycle management. With the release of MLflow 3.0 in 2025, the platform expanded significantly into the GenAI and LLM space, adding first-class tracing for 20+ GenAI frameworks, LLM evaluation with 50+ built-in judges, an AI Gateway for unified model access with cost tracking, and the new LoggedModel entity as a first-class citizen for organizing agents and model variants.

MLflow's one-sentence pitch: it gives any ML or AI team -- from a solo data scientist to a 500-person platform org -- a single, open-source control plane to track experiments, reproduce results, package models, and deploy them to production, without locking into any particular cloud vendor or ML framework.
