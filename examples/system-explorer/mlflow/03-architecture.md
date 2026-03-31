## Architecture
<!-- level: intermediate -->
<!-- references:
- [MLflow Tracking Server Architecture](https://mlflow.org/docs/latest/self-hosting/architecture/tracking-server/) | official-docs
- [Backend Stores](https://mlflow.org/docs/latest/self-hosting/architecture/backend-store/) | official-docs
- [Artifact Stores](https://mlflow.org/docs/latest/self-hosting/architecture/artifact-store/) | official-docs
- [MLflow with Remote Tracking Server](https://medium.com/yelassad/mlflow-with-remote-tracking-server-backend-and-artifact-stores-39912680a464) | blog
-->

### High-Level Design

MLflow follows a client-server architecture with a clear separation between metadata storage (backend store) and file storage (artifact store). The system is designed around a central tracking server that acts as the gateway for all operations -- logging runs, querying experiments, registering models, and serving artifacts.

The architecture can be summarized as a data flow:

```
ML Code (Client) --> Tracking Server (REST API) --> Backend Store (metadata) + Artifact Store (files)
                                                 --> Model Registry (model versions)
```

This design was deliberate: ML workflows produce two fundamentally different types of data. Metadata (parameters, metrics, tags) is small, structured, and needs to be queried efficiently. Artifacts (model files, plots, datasets) are large, unstructured, and need cheap, scalable storage. Trying to put both in the same store would either make queries slow (if using object storage) or make storage expensive (if using a database).

### Key Components

**Tracking Server** -- The central hub that exposes a REST API for all MLflow operations. It receives logging requests from clients, stores metadata in the backend store, and proxies artifact uploads to the artifact store. The server is a Python application (Flask or FastAPI) that can run locally for development or be deployed as a production service behind a load balancer. The server also serves the MLflow UI, a React-based web application for visualizing experiments, comparing runs, and managing models.

The tracking server exists as a separate process because ML training happens everywhere -- Jupyter notebooks, CI/CD pipelines, Spark clusters, Kubernetes jobs -- and all of these need a consistent place to send their data. A centralized server provides that single endpoint while decoupling the storage backend from the client code.

**Backend Store** -- Persists all structured metadata: experiment definitions, run parameters, metrics, tags, and model registry entries. MLflow supports two types: file-based (local filesystem, used for development) and database-backed (SQLite, PostgreSQL, MySQL, MSSQL via SQLAlchemy). The database-backed store is required for the model registry and recommended for any team usage.

The backend store uses SQLAlchemy as its ORM layer, which provides database portability. The schema includes tables for experiments, runs, metrics, parameters, tags, and model registry entities. This relational design enables powerful queries: "find all runs where accuracy > 0.95 and learning_rate < 0.01" translates directly to SQL.

**Artifact Store** -- Handles large file storage for model weights, plots, data files, and any other artifacts produced by runs. MLflow supports local filesystem, Amazon S3, Azure Blob Storage, Google Cloud Storage, SFTP, NFS, and HDFS. Each experiment has a default artifact location, and each run gets a subdirectory within it.

The artifact store is intentionally decoupled from the backend store because artifact access patterns are fundamentally different from metadata access. You write artifacts once (at the end of training), read them occasionally (when deploying or debugging), and they can be gigabytes in size. Object storage (S3, GCS, Azure Blob) is the natural fit -- cheap, scalable, and durable.

**Model Registry** -- A specialized subsystem built on top of the tracking server that manages model versions, lifecycle stages, and aliases. It requires a database-backed backend store (file stores don't support it). The registry adds tables for registered models, model versions, and their associated metadata.

The registry exists as a separate concept because production model management has different requirements than experiment tracking. Experiments are about exploration (many runs, most discarded). The registry is about governance (fewer models, each carefully reviewed and promoted).

**MLflow Client** -- The Python SDK that ML code uses to interact with the tracking server. It comes in two flavors: a fluent API (`mlflow.log_param()`, `mlflow.start_run()`) for simple scripting, and an explicit client API (`MlflowClient()`) for programmatic access. The client handles serialization, batching, async logging, and retries transparently.

### Data Flow

Tracing a typical ML workflow through the system:

1. **Experiment Setup:** A data scientist calls `mlflow.set_experiment("fraud-detection-v2")`. The client sends a REST request to the tracking server, which creates an experiment record in the backend store with a unique ID and default artifact location.

2. **Run Creation:** `mlflow.start_run()` creates a new run record in the backend store with a UUID, start time, and status "RUNNING". The client stores the run ID in a thread-local context so subsequent logging calls know where to send data.

3. **Parameter Logging:** `mlflow.log_param("learning_rate", 0.001)` sends the key-value pair to the tracking server, which inserts it into the `params` table in the backend store. Parameters are immutable -- logging the same key again with a different value raises an error.

4. **Metric Logging:** `mlflow.log_metric("loss", 0.45, step=1)` records the metric with a timestamp and step number. Unlike parameters, metrics accumulate -- you can log "loss" hundreds of times at different steps to build a training curve. The backend store keeps both the full history and a "latest metric" snapshot for fast queries.

5. **Artifact Storage:** `mlflow.log_artifact("model.pkl")` uploads the file to the artifact store under the run's artifact directory. For remote artifact stores, the tracking server can either proxy the upload or provide the client with direct upload credentials.

6. **Model Logging:** `mlflow.sklearn.log_model(model, "model")` packages the model using the MLmodel format -- serializing the model weights, generating an `MLmodel` YAML file with flavor metadata and environment specs, and uploading everything as artifacts.

7. **Model Registration:** `mlflow.register_model(model_uri, "fraud-detector")` creates or updates a registered model in the model registry. It creates a new version linked to the run's model artifact, with an initial stage of "None".

8. **Model Promotion:** An ML engineer reviews the model in the UI, compares its metrics against the current production model, and transitions it to "Production" stage via the registry API.

### Design Decisions

**REST API over Direct Database Access:** Clients never talk to the backend store directly -- everything goes through the tracking server's REST API. This provides access control, schema evolution, and the ability to swap storage backends without changing client code. The trade-off is an extra network hop for every operation, but MLflow mitigates this with batched and async logging.

**Pluggable Storage Backends:** Both the backend store and artifact store are abstracted behind interfaces (`AbstractStore` for tracking, artifact repository interfaces for artifacts). This means you can run MLflow with SQLite locally, PostgreSQL in staging, and a managed Databricks service in production -- all without changing your ML code. The abstraction adds complexity but enables deployment flexibility.

**Separation of Metadata and Artifacts:** This is perhaps MLflow's most important architectural decision. Metadata (params, metrics, tags) needs to be small and queryable. Artifacts (models, plots) need to be large and durable. Putting them in the same store would compromise one or the other. The separation means you can use PostgreSQL for fast metadata queries and S3 for cheap, unlimited artifact storage.

**Stateless Tracking Server:** The tracking server is stateless -- all state lives in the backend and artifact stores. This means you can run multiple tracking server instances behind a load balancer for high availability, and a server crash doesn't lose data. This was a deliberate choice for production reliability.

**Fluent API with Thread-Local Context:** MLflow's fluent API (`mlflow.log_param()`) uses thread-local storage to track the active run. This makes the API clean for interactive use (no need to pass run IDs everywhere) but can cause confusion in multi-threaded or async code where runs might leak across threads. The explicit `MlflowClient` API avoids this by requiring run IDs for every operation.
