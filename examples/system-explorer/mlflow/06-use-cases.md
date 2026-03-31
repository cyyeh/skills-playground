## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
<!-- references:
- [MLflow Use Cases](https://mlflow.org/docs/latest/) | docs
- [Databricks Managed MLflow](https://www.databricks.com/product/managed-mlflow) | vendor
- [MLflow on AWS SageMaker](https://docs.aws.amazon.com/sagemaker/latest/dg/mlflow.html) | cloud
-->

### Use Case 1: Experiment Tracking for a Data Science Team

**Scenario:** A financial services company has a team of 12 data scientists building fraud detection models. They are using Jupyter notebooks and passing results around via Slack and spreadsheets. Nobody can reproduce last week's best result.

**How MLflow helps:**
1. The team deploys a shared MLflow tracking server backed by PostgreSQL and S3.
2. Each data scientist adds `mlflow.autolog()` to their notebooks. Every training run automatically logs hyperparameters, metrics, and model artifacts.
3. The MLflow UI lets the team compare runs side by side -- sorting by F1 score, filtering by model type, and visualizing metric trends across epochs.
4. When a data scientist finds a promising approach, they share the run ID, and any teammate can load the exact model and reproduce the result.

**Impact:** Experiment reproducibility goes from "almost never" to "always." Model comparison time drops from hours of spreadsheet wrangling to seconds of UI filtering.

### Use Case 2: Model Registry and CI/CD for Production Deployment

**Scenario:** An e-commerce platform serves personalized product recommendations to 50 million users. New models need to be tested, approved, and deployed without disrupting the serving pipeline.

**How MLflow helps:**
1. After training, the best model is registered in the MLflow Model Registry as a new version of "recommendation-engine."
2. A CI pipeline runs automated evaluation: accuracy tests, latency benchmarks, and bias checks. If the model passes, it is aliased as "challenger."
3. The challenger model is deployed alongside the current "champion" in an A/B test using MLflow's deployment tools and Kubernetes.
4. After a week of live testing, if the challenger outperforms, the alias is flipped: the challenger becomes the champion, and the old champion is archived.

**Impact:** The team deploys new models weekly with zero-downtime rollouts. Model lineage is fully traceable -- from training data to production serving.

### Use Case 3: LLM Application Development and Evaluation

**Scenario:** A SaaS company is building a customer support chatbot using GPT-4 and a RAG (Retrieval-Augmented Generation) pipeline. They need to evaluate prompt changes, retrieval quality, and response safety before releasing updates.

**How MLflow helps:**
1. The team enables `mlflow.openai.autolog()` and `mlflow.langchain.autolog()` to capture traces of every LLM call, retrieval step, and tool invocation.
2. When a prompt engineer modifies the system prompt, they run `mlflow.evaluate()` against a golden dataset with scorers for correctness, relevance, and safety.
3. The MLflow UI shows a side-by-side comparison of the old and new prompt versions, with per-example traces and aggregate scores.
4. The AI Gateway manages API keys centrally and enforces a daily budget limit to prevent cost overruns during development.

**Impact:** Prompt iteration speed doubles because engineers can see exactly how each change affects response quality. The safety scorer catches problematic responses before they reach production.

### Use Case 4: Multi-Framework ML Pipeline with Spark

**Scenario:** A telecommunications company processes call records using Apache Spark for feature engineering, trains models with XGBoost for churn prediction, and deploys them as REST APIs for the CRM system.

**How MLflow helps:**
1. The Spark ETL job logs feature statistics and data lineage as MLflow run artifacts.
2. XGBoost training uses `mlflow.xgboost.autolog()` to capture all hyperparameters, tree metrics, and the trained model in the `xgboost` flavor.
3. The model is registered and then served using `mlflow models serve`, which loads the XGBoost model via the universal `pyfunc` flavor and exposes a JSON-in/JSON-out REST endpoint.
4. The CRM system calls the `/invocations` endpoint in real time to score customers and trigger retention campaigns.

**Impact:** The team uses best-in-class tools at each stage (Spark for data, XGBoost for modeling) without writing any glue code for deployment. The `pyfunc` flavor bridges the framework gap.
