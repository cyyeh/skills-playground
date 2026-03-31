## Overview
<!-- level: beginner -->
<!-- references:
- [MLflow Official Documentation](https://mlflow.org/docs/latest/) | official-docs
- [Introducing MLflow: an Open Source Machine Learning Platform](https://www.databricks.com/blog/2018/06/05/introducing-mlflow-an-open-source-machine-learning-platform.html) | blog
- [MLflow GitHub Repository](https://github.com/mlflow/mlflow) | github
-->

MLflow is an open-source platform for managing the entire machine learning lifecycle -- from experiment tracking through model deployment and monitoring. Think of it as "Git for machine learning" -- where Git tracks code changes, MLflow tracks everything else in an ML project: which hyperparameters you tried, how well each model performed, which dataset version you used, and which model is currently serving production traffic.

Created at Databricks in 2018 by Matei Zaharia (the creator of Apache Spark) and later donated to the Linux Foundation, MLflow was born from the observation that ML development is fundamentally harder to manage than traditional software development. Every training run produces artifacts (model weights, plots, data snapshots) and metadata (parameters, metrics, tags) that need to be tracked, compared, and reproduced. Without a system to manage this, teams drown in spreadsheets, lost notebooks, and the dreaded "which model is in production?" question.

### What It Is

MLflow is an ML lifecycle management platform that provides four core capabilities: experiment tracking (recording parameters, metrics, and artifacts from training runs), model packaging (saving models in a standard format that works across frameworks), a model registry (versioning and staging models for production), and model deployment (serving models as REST APIs or batch jobs). With over 60 million monthly downloads, it has become the de facto standard for MLOps in both research and industry.

### Who It's For

MLflow is built for data scientists who want to stop losing track of experiments, ML engineers who need to deploy models reliably, and platform teams who want a standard way to manage ML workflows across their organization. It works with any ML library (scikit-learn, PyTorch, TensorFlow, XGBoost, LLMs) and any infrastructure (local, cloud, Kubernetes). Whether you are a solo researcher running experiments on a laptop or a team of fifty deploying models to millions of users, MLflow scales to your needs.

### The One-Sentence Pitch

MLflow gives you a single platform to track experiments, package models, manage versions, and deploy to production -- all open source, framework-agnostic, and designed to work the way ML teams actually work.
