## Architecture
<!-- level: intermediate -->
<!-- references:
- [MLflow Architecture Overview](https://mlflow.org/docs/latest/self-hosting/architecture/overview/) | official-docs
- [MLflow Tracking Server](https://mlflow.org/docs/latest/self-hosting/architecture/tracking-server/) | official-docs
- [Backend Stores](https://mlflow.org/docs/latest/self-hosting/architecture/backend-store/) | official-docs
- [Artifact Stores](https://mlflow.org/docs/latest/self-hosting/architecture/artifact-store/) | official-docs
-->

### System Overview

MLflow's architecture follows a client-server design with three core infrastructure components: the Tracking Server, the Backend Store, and the Artifact Store. These can be deployed together on a single machine or distributed across separate hosts for production scalability.

### Tracking Server

The MLflow Tracking Server is a FastAPI application that exposes REST APIs for logging and querying experiment data. It serves two roles: (1) an API server that accepts log calls from the MLflow client SDK and queries from the UI, and (2) a web server hosting the MLflow UI -- a React-based single-page application for visual exploration of experiments, runs, and models. The server can also operate as an artifact proxy, relaying artifact upload/download requests so clients never need direct access to the underlying object store.

### Backend Store

The Backend Store persists structured metadata: experiments, runs, parameters, metrics, tags, and model registry entries. MLflow supports two categories of backend:

- **File-based store:** SQLite (default) writes metadata to a local `mlruns/` directory. Simple for local development but unsuitable for concurrent production use due to locking limitations.
- **Database-based store:** PostgreSQL, MySQL, or MSSQL via SQLAlchemy. These provide proper indexing, concurrent access, and transactional guarantees required for team-scale and production deployments.

### Artifact Store

The Artifact Store handles large, unstructured files -- model binaries, images, datasets, plots. By default, artifacts live on the local filesystem alongside the backend store. For production, MLflow supports remote artifact stores: Amazon S3, Azure Blob Storage, Google Cloud Storage, HDFS, SFTP, and NFS. The tracking server can operate in "artifact proxy" mode, where all artifact traffic flows through the server rather than requiring clients to have direct credentials to the object store.

### Model Registry

The Model Registry is a logical layer built on top of the Backend Store and Artifact Store. It provides model versioning, alias management (@champion, @challenger), tag-based metadata, and lifecycle stage tracking. Each registered model version maintains lineage links back to the MLflow run and logged model that produced it.

### Deployment Patterns

MLflow supports several deployment topologies:

1. **Local mode:** Client, tracking server, backend store, and artifact store all on one machine. Good for solo experimentation.
2. **Remote tracking server:** A central tracking server with a database backend and remote artifact store. Clients log over HTTP. The standard team deployment.
3. **Tracking server with artifact proxy:** The server proxies artifact operations, so clients only need HTTP access to the server -- no object store credentials needed. Recommended for security-sensitive environments.
4. **Managed MLflow (Databricks):** A fully managed version with integrated governance, access control, and Unity Catalog integration. Removes all infrastructure management.

### AI Gateway Architecture

The AI Gateway sits as a reverse-proxy layer in front of LLM providers. It maintains route configurations mapping logical endpoint names to provider-specific credentials and models. Each request flows through the gateway, which handles authentication, rate limiting, cost metering, and automatic trace capture before forwarding to the provider. The gateway integrates natively with MLflow Tracing, so every proxied call automatically becomes a linked trace in the experiment context.
