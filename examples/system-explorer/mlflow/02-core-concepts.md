## Core Concepts
<!-- level: beginner -->
<!-- references:
- [MLflow Tracking Documentation](https://mlflow.org/docs/latest/tracking/) | official-docs
- [ML Model Registry](https://mlflow.org/docs/latest/ml/model-registry/) | official-docs
- [MLflow Models](https://mlflow.org/docs/latest/ml/model/) | official-docs
-->

### Experiment

**Definition:** An experiment is a named container for a collection of related training runs. It groups runs that share a common goal -- for example, "fraud-detection-v2" or "sentiment-classifier-bert".

**Analogy:** Think of an experiment as a lab notebook. A scientist has one notebook per research question. Inside that notebook, they record every attempt (run) they make -- different reagent amounts, temperatures, and observations. The notebook keeps everything organized so they can flip back and compare what worked. An MLflow experiment is that notebook for your ML project.

**Why it matters:** Without experiments, all your training runs pile up in one undifferentiated list. Experiments provide the organizational boundary that lets you find, compare, and share related work. They also define the default artifact storage location for all runs within them.

### Run

**Definition:** A run is a single execution of ML code -- one training session with specific parameters, producing specific metrics and artifacts. Every time you call `mlflow.start_run()`, you create a new run within the active experiment.

**Analogy:** If the experiment is the lab notebook, a run is a single page in that notebook. It records exactly what you did (parameters), what happened (metrics over time), and what you produced (artifacts like model files or plots). Each page has a unique ID so you can always reference it later.

**Why it matters:** Runs are the atomic unit of ML work in MLflow. Every parameter, metric, artifact, and tag is associated with a run. When you compare model performance, you are comparing runs. When you deploy a model, it came from a specific run. The run is the single source of truth for "what happened during this training session."

### Parameters

**Definition:** Parameters are key-value pairs that describe the inputs to a training run -- hyperparameters like learning rate, batch size, number of epochs, or model architecture choices. They are logged once per run and are immutable after logging.

**Analogy:** Parameters are the recipe ingredients. When a chef tries a new cake recipe, they write down "2 cups flour, 1 cup sugar, 350F oven." If the cake turns out great, they know exactly what to reproduce. If it fails, they know what to change next time.

**Why it matters:** Reproducibility is the foundation of good ML practice. Parameters capture the "what did I configure?" question. Combined with code versioning and data tracking, they let you recreate any training run exactly. MLflow supports values up to 6000 characters, so you can log complex configuration objects as JSON strings.

### Metrics

**Definition:** Metrics are numerical measurements that track model performance during and after training -- accuracy, loss, F1 score, latency, or any custom measurement. Unlike parameters, metrics can be logged multiple times at different steps (epochs), creating a time series.

**Analogy:** Metrics are the vital signs monitor in a hospital. Just as a heart monitor continuously records heart rate, blood pressure, and oxygen levels over time, metrics track your model's health during training. You can see if accuracy is improving, if loss is plateauing, or if overfitting is starting -- all as the training progresses.

**Why it matters:** Metrics are how you answer "is this model better than the last one?" They support step-based logging, so you can track loss at every epoch and plot learning curves. MLflow stores the full metric history, letting you compare training dynamics across runs -- not just final scores.

### Artifacts

**Definition:** Artifacts are output files produced by a run -- model weights, plots, data samples, configuration files, or any other file you want to preserve. They are stored in an artifact store (local filesystem, S3, GCS, Azure Blob) separate from the metadata.

**Analogy:** Artifacts are the physical products from your lab experiment. The notebook (run metadata) records what you did, but the actual test tube of synthesized compound (model file), the microscope photographs (plots), and the data printouts (evaluation results) are the artifacts. You store them carefully because they are what you actually ship to production.

**Why it matters:** Models are large binary files (megabytes to gigabytes) that don't belong in a metadata database. The artifact store handles this separation cleanly -- metadata (parameters, metrics, tags) goes to the backend store (fast, queryable), while artifacts go to object storage (scalable, cheap). This separation is what makes MLflow work at scale.

### Model (MLmodel Format)

**Definition:** An MLflow Model is a standard packaging format for ML models. It wraps the model's weights with metadata (an `MLmodel` YAML file) describing which frameworks ("flavors") can load it, the model's input/output signature, its dependencies, and how to serve it.

**Analogy:** Think of the MLmodel format as a shipping container for models. Just as a shipping container has a standardized size and labeling system so any port can handle it regardless of what's inside, the MLmodel format provides a standardized wrapper so any deployment system can serve the model regardless of whether it's a scikit-learn pipeline, a PyTorch neural network, or an XGBoost tree.

**Why it matters:** The MLmodel format solves the "how do I deploy this?" problem. Every ML framework has its own save/load format. MLflow's model packaging adds a universal layer on top: the `pyfunc` flavor. Any MLflow model can be loaded as a `pyfunc` and called with `model.predict(data)`, regardless of the underlying framework. This is what makes framework-agnostic deployment possible.

### Model Registry

**Definition:** The model registry is a centralized store for managing model versions, lifecycle stages, and metadata. You register a model by name, create versions from training runs, add descriptions and tags, assign aliases (like "champion" or "challenger"), and track which version is serving production traffic.

**Analogy:** The model registry is like a wine cellar with a catalog system. Each wine (model) has a name and vintage year (version). The sommelier (ML engineer) tracks which bottles are aging (staging), which are ready to serve (production), and which have been retired (archived). The catalog lets anyone look up a wine's origin, tasting notes, and current status without opening every bottle.

**Why it matters:** In production ML, the question "which model is deployed?" needs a definitive answer. The model registry provides that answer with a full audit trail: who registered this version, when, from which run, with what performance metrics. It enables governed model promotion workflows where a model moves from "None" to "Staging" to "Production" with human review at each step.

### How They Fit Together

When you run an ML training script, MLflow creates a run inside your experiment. During training, parameters (hyperparameters) are logged once, and metrics (accuracy, loss) are logged at each step. When training finishes, the trained model is saved as an artifact using the MLmodel format, which packages it with its dependencies and serving instructions. If the model performs well, you register it in the model registry under a descriptive name, creating a new version. The registry tracks the model's lifecycle as it moves from experimentation through staging to production. Throughout this process, the tracking server stores metadata in the backend store and files in the artifact store, providing a complete, queryable record of every experiment your team has ever run.
