## Overview
<!-- level: beginner -->
<!-- references:
- [MLflow Official Documentation](https://mlflow.org/docs/latest/) | official-docs
- [MLflow GitHub Repository](https://github.com/mlflow/mlflow) | github
- [MLflow 3.0: Build, Evaluate, and Deploy Generative AI with Confidence](https://www.databricks.com/blog/mlflow-30-unified-ai-experimentation-observability-and-governance) | blog
- [MLflow: The Complete Guide](https://www.run.ai/guides/machine-learning-operations/mlflow) | tutorial
-->

MLflow is an open-source platform for managing the entire machine learning and AI lifecycle. Originally created at [Databricks](https://www.databricks.com/) in 2018 to address the chaos of tracking ML experiments and deploying models, it has grown into the most widely adopted open-source MLOps platform with over 24,900 GitHub stars and 900+ contributors. MLflow 3.x has expanded its scope significantly beyond traditional ML to embrace generative AI, LLM observability, and agent engineering, making it a unified platform for both classical ML and modern AI applications.

At its core, MLflow solves a fundamental problem: machine learning development is inherently experimental, and without proper tooling, teams lose track of what they tried, what worked, and why. Every data scientist has experienced the frustration of running dozens of experiments with different hyperparameters, only to discover weeks later that they cannot reproduce their best result. MLflow provides the infrastructure to make ML development reproducible, collaborative, and production-ready.

### What It Is

MLflow is a platform for the complete AI engineering lifecycle -- like a version-controlled lab notebook combined with a deployment pipeline for machine learning. It tracks every experiment you run, packages models in a standardized format that works everywhere, manages model versions through a central registry, and provides observability for LLM-powered applications in production.

### Who It's For

MLflow serves a broad spectrum of practitioners. **Data scientists** use it to track experiments and compare model performance across runs. **ML engineers** rely on it to package models with reproducible environments and deploy them to production. **Platform teams** use the tracking server and model registry to provide shared infrastructure for their organization. **GenAI engineers** leverage its tracing and evaluation capabilities to debug and monitor LLM applications and AI agents. The platform scales from individual researchers running experiments on a laptop to enterprise teams managing thousands of models across multiple environments.

### The One-Sentence Pitch

MLflow is the open-source standard for experiment tracking, model packaging, and AI observability that lets your team go from prototype to production without losing track of what works and why.
