## Architecture
<!-- level: intermediate -->
<!-- references:
- [MLflow Tracking Server Architecture](https://mlflow.org/docs/latest/self-hosting/architecture/tracking-server/) | docs
- [MLflow REST API](https://mlflow.org/docs/latest/rest-api.html) | docs
- [MLflow AI Gateway](https://mlflow.org/ai-gateway) | docs
-->

### High-Level Component Diagram

```
                          +--------------------+
                          |   Client Code      |
                          | (Python/R/Java/    |
                          |  REST API)         |
                          +---------+----------+
                                    |
                           HTTP / gRPC
                                    |
                          +---------v----------+
                          |  MLflow Tracking    |
                          |      Server         |
                          |  (Flask/Gunicorn)   |
                          +----+--------+------+
                               |        |
                   +-----------+        +-----------+
                   |                                |
          +--------v--------+            +----------v---------+
          |  Backend Store   |            |   Artifact Store    |
          | (metadata)       |            |   (files/models)    |
          | - SQLite         |            | - Local filesystem  |
          | - MySQL          |            | - Amazon S3         |
          | - PostgreSQL     |            | - Azure Blob        |
          | - SQL Server     |            | - Google Cloud Stor.|
          +--------+---------+            | - HDFS / DBFS       |
                   |                      +----------+----------+
                   |                                 |
          +--------v---------+            +----------v---------+
          | Model Registry   |            |  Artifact Proxy     |
          | (versions, alias,|            |  (optional HTTP     |
          |  tags, lineage)  |            |   passthrough)      |
          +------------------+            +--------------------+

                          +--------------------+
                          |   AI Gateway       |
                          | (LLM proxy layer)  |
                          | - Route to LLM     |
                          |   providers        |
                          | - Credential mgmt  |
                          | - Usage tracking   |
                          | - Rate limiting    |
                          +--------------------+
```

### Components in Detail

#### Tracking Server

The Tracking Server is an HTTP server (built on Flask, typically served via Gunicorn or Uvicorn) that exposes the MLflow REST API. It accepts requests from client libraries, writes metadata to the backend store, and manages artifact storage.

The server can run in several configurations:
1. **Local mode:** No server; the client writes directly to the local filesystem (`./mlruns`).
2. **Remote tracking server:** A shared server that teams point their clients at, centralizing all experiment data.
3. **Tracking server with artifact proxy:** The server proxies artifact read/write requests so clients never need direct access to the underlying object store (S3, Azure Blob, etc.).

#### Backend Store

The backend store persists structured metadata: experiments, runs, parameters, metrics, tags, and model registry data. MLflow supports:

- **File store:** Flat files under `./mlruns`. Suitable only for local, single-user usage.
- **Database store:** Any SQLAlchemy-compatible database -- SQLite, PostgreSQL, MySQL, or Microsoft SQL Server. Required for the Model Registry and recommended for any multi-user deployment.

The backend store schema uses tables for experiments, runs, params, metrics, tags, model versions, and registered models.

#### Artifact Store

The artifact store persists large, unstructured files: serialized models, plots, datasets, evaluation reports. It is completely separate from the backend store and supports:

- Local filesystem
- Amazon S3 (and S3-compatible stores like MinIO)
- Azure Blob Storage
- Google Cloud Storage
- HDFS
- Databricks DBFS
- FTP/SFTP

When the tracking server runs with `--serve-artifacts`, it acts as an HTTP proxy to the artifact store, so clients only need network access to the tracking server.

#### Model Registry

The Model Registry is a logical layer on top of the backend store (database-backed only). It provides:

- **Registered models:** Named entries (e.g., "fraud-detector") with descriptions and tags.
- **Model versions:** Immutable snapshots linked to a specific run and artifact path.
- **Aliases:** Mutable labels like "champion" or "challenger" that point to a specific version.
- **Tags and annotations:** Metadata for governance, review status, and documentation.

#### AI Gateway

Introduced in MLflow 3.x, the AI Gateway is a centralized proxy for LLM API calls. It:

- Routes requests to multiple LLM providers (OpenAI, Anthropic, Cohere, etc.) through a unified API.
- Manages credentials centrally so application code never contains API keys.
- Tracks usage, latency, and cost per route.
- Enforces rate limits and budget policies (daily, weekly, monthly).
- Integrates with MLflow Tracing for end-to-end observability.

### Data Flow

1. **Logging a run:** Client calls `mlflow.start_run()`. The tracking server creates a run record in the backend store. As the client logs params, metrics, and artifacts, each is written via REST API to the appropriate store.

2. **Querying results:** The tracking UI (or API client) queries the backend store for runs, filters by metric thresholds, and renders comparisons. Artifact downloads are served through the tracking server (proxied) or directly from the artifact store.

3. **Registering a model:** A user or CI pipeline calls `mlflow.register_model()`, which creates a model version entry in the backend store linked to the run's artifact path. Aliases are then assigned to control which version serves production traffic.

4. **Serving a model:** The deployment tools read the model artifacts from the artifact store, load the model using its flavor, and expose it via a REST endpoint (Docker container, Kubernetes pod, or cloud-managed endpoint).

5. **LLM gateway flow:** Application code sends a chat/completion request to the AI Gateway. The gateway resolves the route, injects credentials, forwards the request to the LLM provider, and logs the trace back to the tracking server for observability.
