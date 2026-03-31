## Architecture
<!-- level: intermediate -->
<!-- references:
- [MLflow Architecture Overview](https://mlflow.org/docs/latest/self-hosting/architecture/overview/) | official-docs
- [MLflow Backend Stores](https://mlflow.org/docs/latest/self-hosting/architecture/backend-store/) | official-docs
- [MLflow Tracking Server](https://mlflow.org/docs/latest/self-hosting/architecture/tracking-server/) | official-docs
- [MLflow Self-Hosting Guide](https://mlflow.org/docs/latest/self-hosting/) | official-docs
-->

### High-Level Design

MLflow follows a client-server architecture with a clean separation between metadata storage and artifact storage. The system is designed around three layers: a **client SDK layer** that provides language-specific APIs (Python, TypeScript, Java, R), a **service layer** consisting of the Tracking Server that exposes REST endpoints and hosts the web UI, and a **storage layer** split into a Backend Store (relational database for metadata) and an Artifact Store (object storage for large files). This separation is deliberate -- metadata queries (searching runs, comparing metrics) have very different access patterns from artifact retrieval (downloading a 2GB model file), so the two storage systems can be scaled and optimized independently.

The architecture is intentionally modular. You can run everything locally on a single machine with SQLite and the local filesystem, or deploy a production topology with a PostgreSQL backend, S3 artifact storage, and a load-balanced tracking server cluster. The same client code works unchanged across these configurations -- you only change a URI string.

### Key Components

**MLflow Client SDK** -- The primary interface through which users interact with MLflow. Available in Python (`mlflow` package), TypeScript, Java, and R. The SDK provides both a fluent API (top-level functions like `mlflow.start_run()`, `mlflow.log_metric()`) and a client API (`MlflowClient` class) for programmatic access. The fluent API manages thread-local run context automatically, while the client API gives explicit control over run IDs. The SDK exists because ML code runs in diverse environments (notebooks, scripts, distributed training jobs) and needs a consistent way to communicate with the tracking infrastructure regardless of context.

**Tracking Server** -- A [FastAPI-based](https://fastapi.tiangolo.com/) HTTP server that mediates all communication between clients and storage. It exposes REST API endpoints for creating experiments, logging runs, querying metrics, and managing the model registry. The server also hosts the MLflow web UI for visual exploration. The tracking server exists because teams need a shared, centralized point of access with authentication, access control, and network isolation -- direct database access from every data scientist's laptop would be a security and operational nightmare. The server uses protobuf-based request/response messages parsed from JSON, with schema validation on every request.

**Backend Store** -- A relational database that persists all metadata: experiments, runs, parameters, metrics, tags, registered models, model versions, aliases, and traces. MLflow supports [SQLAlchemy-compatible](https://www.sqlalchemy.org/) databases including PostgreSQL, MySQL, SQLite, and MSSQL. The store is implemented through an abstract `AbstractStore` interface with concrete implementations: `SqlAlchemyStore` for database backends, `FileStore` for file-based storage (legacy), and `RestStore` for client-side proxying through the tracking server. The backend store exists as a separate component because metadata is highly relational (runs belong to experiments, metrics belong to runs, model versions belong to registered models) and benefits from SQL queries, transactions, and indexes. A specialized `SqlLatestMetric` table caches the most recent value of each metric key per run, avoiding expensive aggregation queries during common search operations.

**Artifact Store** -- An object storage system for large binary files: model weights, images, data files, and other run outputs. Supported backends include local filesystem, Amazon S3, Azure Blob Storage, Google Cloud Storage, HDFS, and SFTP. The artifact store is implemented through an abstract `ArtifactRepository` interface with backend-specific implementations (`S3ArtifactRepository`, `LocalArtifactRepository`, etc.). The artifact store is separated from the backend store because model files can be gigabytes in size -- storing them in a relational database would be impractical and expensive. Object storage systems are designed for exactly this use case: cheap, durable, high-throughput storage of large blobs.

**Model Registry** -- A governance layer on top of the tracking system that manages the lifecycle of registered models. It provides named model containers with auto-incrementing version numbers, mutable aliases (like `@champion`), tags, and markdown annotations. The registry is backed by its own `AbstractModelRegistryStore` (with `SqlAlchemyModelRegistryStore` as the primary implementation) that shares the same database as the tracking backend store but uses separate tables. The model registry exists because experiment tracking answers "what did we try?" while the registry answers "what are we running in production?" -- these are fundamentally different concerns requiring different workflows and access patterns.

**Tracing System** -- An [OpenTelemetry-compatible](https://opentelemetry.io/) observability layer for GenAI applications. The tracing system captures request-level execution traces consisting of hierarchical spans. It uses a `TracerProviderWrapper` that can operate in isolated mode (MLflow manages its own tracer provider) or unified mode (shares the global OpenTelemetry provider). Span processors export trace data to the backend store or external destinations. The tracing system exists because LLM applications have fundamentally different observability needs than traditional ML: you need to see every intermediate step in a chain (retrieval, prompt formatting, LLM call, tool use) to debug quality issues, not just final model metrics.

**Web UI** -- A browser-based interface served by the tracking server that lets users visually explore experiments, compare runs, inspect artifacts, manage the model registry, and view traces. The UI provides metric visualization with charts, run comparison tables, artifact browsers, and model version dashboards. The web UI exists because while the API is powerful for automation, human decision-making (which model to deploy, why a run failed, comparing experiment results) benefits enormously from visual presentation.

### Data Flow

**Experiment Tracking Flow (a training run):**

1. A data scientist's Python script calls `mlflow.set_experiment("churn-prediction")` and `mlflow.start_run()`.
2. The SDK sends a `CreateRun` REST request to the Tracking Server with the experiment ID, a generated run UUID, and initial tags.
3. The Tracking Server validates the request, then calls `SqlAlchemyStore.create_run()` which inserts a `SqlRun` row into the backend database with status `RUNNING`.
4. During training, the script calls `mlflow.log_param("lr", 0.001)` and `mlflow.log_metric("accuracy", 0.94, step=10)`. Each call sends a REST request; the server persists params and metrics to their respective database tables.
5. At the end, the script calls `mlflow.sklearn.log_model(model, name="churn-model")`. The SDK serializes the model to a local temporary directory (creating `model.pkl`, `MLmodel`, `conda.yaml`, etc.), then uploads the entire directory to the artifact store at the run's artifact URI.
6. `mlflow.end_run()` sends a status update; the server marks the run as `FINISHED`.

**Model Registry Flow (promoting to production):**

1. An ML engineer finds the best run in the UI and calls `mlflow.register_model("runs:/<run_id>/churn-model", "ChurnPredictor")`.
2. The SDK sends a `CreateModelVersion` request to the tracking server, which creates a `SqlModelVersion` row linking to the run's artifact location. The version number auto-increments.
3. After validation, the engineer calls `client.set_registered_model_alias("ChurnPredictor", "champion", version=3)`, updating the alias pointer.
4. A serving system loads the production model using `mlflow.pyfunc.load_model("models:/ChurnPredictor@champion")`, which resolves the alias to a version, downloads artifacts from the artifact store, and loads the model using the appropriate flavor loader.

**Tracing Flow (GenAI application):**

1. A GenAI application calls `mlflow.openai.autolog()` at startup, which instruments the OpenAI client.
2. When a user request arrives, the auto-instrumented client creates a root span and attaches it to the trace context.
3. Each LLM call, tool invocation, and retrieval step creates child spans with inputs, outputs, and timing. Spans are managed through OpenTelemetry's context propagation.
4. When the request completes, span processors asynchronously export the completed trace to the backend store via the tracking server.
5. Engineers view traces in the MLflow UI, filtering by experiment, latency, or error status.

### Design Decisions

**Metadata and artifacts separated by design.** Many competing systems store everything together. MLflow's split means you can use a fast, queryable Postgres database for experiment metadata while storing multi-gigabyte model artifacts in cheap S3 storage. This also means the tracking server never needs to proxy large file transfers -- artifact uploads can go directly to S3 -- reducing server load and latency.

**The pyfunc universal interface.** Instead of requiring deployment tools to understand every ML framework, MLflow defines a single `python_function` flavor that any model can implement. This means a Kubernetes serving system only needs to know how to load and call a pyfunc model, and it automatically works with scikit-learn, PyTorch, TensorFlow, and custom models. This is the key architectural decision that makes MLflow's model packaging genuinely portable.

**Protobuf for API contracts.** The tracking server uses Protocol Buffer message definitions as its API schema, parsed from JSON. This provides strong typing, backward compatibility through field numbering, and auto-generated client code. It is an unusual choice for a Python-first project but provides a much more robust API contract than ad-hoc JSON parsing.

**OpenTelemetry for tracing.** Rather than building a proprietary tracing format, MLflow adopted OpenTelemetry as its tracing foundation. This means MLflow traces are compatible with the broader observability ecosystem (Jaeger, Zipkin, Datadog) and that distributed tracing across services works out of the box. The `TracerProviderWrapper` dual-mode design (isolated vs. unified) lets MLflow coexist with existing OpenTelemetry instrumentation without conflicts.

**Pluggable store backends.** The `AbstractStore` and `ArtifactRepository` interfaces allow MLflow to support diverse infrastructure without changing client code. A team can start with SQLite and local files, migrate to Postgres and S3 as they grow, and eventually move to a managed Databricks deployment -- all without modifying their training scripts. This flexibility is a major reason for MLflow's adoption.
