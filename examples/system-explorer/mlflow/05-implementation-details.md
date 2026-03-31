## Implementation Details
<!-- level: advanced -->
<!-- references:
- [MLflow Tracking Quickstart](https://mlflow.org/docs/latest/ml/tracking/quickstart/) | official-docs
- [MLflow Python API Reference](https://mlflow.org/docs/latest/python_api/mlflow.html) | official-docs
- [MLflow Source Code](https://github.com/mlflow/mlflow) | github
- [MLflow Backend Stores](https://mlflow.org/docs/latest/self-hosting/architecture/backend-store/) | official-docs
-->

### Getting Started

**Installation:**
```bash
pip install mlflow
```

**Quick experiment tracking:**
```python
import mlflow
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Set up experiment
mlflow.set_experiment("iris-classification")

# Prepare data
X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train with manual logging
params = {"solver": "lbfgs", "max_iter": 1000, "C": 1.0}

with mlflow.start_run():
    mlflow.log_params(params)
    
    model = LogisticRegression(**params)
    model.fit(X_train, y_train)
    
    accuracy = accuracy_score(y_test, model.predict(X_test))
    mlflow.log_metric("accuracy", accuracy)
    
    model_info = mlflow.sklearn.log_model(model, name="iris_model")
    mlflow.set_tag("Training Info", "Basic LR model for iris data")
```

**Autologging (zero-code tracking):**
```python
import mlflow
mlflow.sklearn.autolog()

# Just train -- MLflow captures everything automatically
model = LogisticRegression(solver="lbfgs", max_iter=1000)
model.fit(X_train, y_train)
```

**Starting the tracking server:**
```bash
# Local development
mlflow server --port 5000

# Production with PostgreSQL backend and S3 artifacts
mlflow server \
    --backend-store-uri postgresql://user:pass@host/mlflow \
    --default-artifact-root s3://my-mlflow-bucket/artifacts \
    --host 0.0.0.0 \
    --port 5000
```

**Loading a model for inference:**
```python
loaded_model = mlflow.pyfunc.load_model(model_info.model_uri)
predictions = loaded_model.predict(X_test)
```

### Configuration Essentials

| Setting | Default | What it controls | When to change |
|---------|---------|-----------------|----------------|
| `MLFLOW_TRACKING_URI` | `./mlruns` | Where the client sends tracking data | Always in team settings (point to remote server) |
| `MLFLOW_EXPERIMENT_NAME` | `Default` | Active experiment for runs | Set per project/notebook |
| `MLFLOW_ENABLE_ASYNC_LOGGING` | `false` | Batch and async metric logging | High-frequency logging scenarios |
| `MLFLOW_ARTIFACT_ROOT` | `./mlruns` | Default artifact storage location | Production (set to S3/GCS/Azure) |
| `MLFLOW_S3_ENDPOINT_URL` | AWS default | S3-compatible endpoint | MinIO, LocalStack, or non-AWS S3 |
| `MLFLOW_HTTP_REQUEST_TIMEOUT` | `120` | API request timeout in seconds | Slow networks or large artifact uploads |
| `MLFLOW_TRACKING_USERNAME` | None | Basic auth username for tracking server | Secured deployments |
| `MLFLOW_TRACKING_PASSWORD` | None | Basic auth password for tracking server | Secured deployments |

### Code Patterns

**Comparing runs and selecting the best model:**
```python
from mlflow import MlflowClient

client = MlflowClient()

# Search for best run by accuracy
best_run = client.search_runs(
    experiment_ids=["1"],
    filter_string="metrics.accuracy > 0.9",
    order_by=["metrics.accuracy DESC"],
    max_results=1
)[0]

print(f"Best run: {best_run.info.run_id}, accuracy: {best_run.data.metrics['accuracy']}")

# Register the best model
model_uri = f"runs:/{best_run.info.run_id}/model"
mlflow.register_model(model_uri, "fraud-detector")
```

**Nested runs for hyperparameter tuning:**
```python
import mlflow
from sklearn.model_selection import ParameterGrid

param_grid = {"C": [0.1, 1.0, 10.0], "solver": ["lbfgs", "liblinear"]}

with mlflow.start_run(run_name="hp-search") as parent:
    for params in ParameterGrid(param_grid):
        with mlflow.start_run(run_name=f"C={params['C']}", nested=True):
            mlflow.log_params(params)
            model = LogisticRegression(**params)
            model.fit(X_train, y_train)
            accuracy = accuracy_score(y_test, model.predict(X_test))
            mlflow.log_metric("accuracy", accuracy)
```

**Model registry workflow:**
```python
from mlflow import MlflowClient

client = MlflowClient()

# Create registered model
client.create_registered_model("fraud-detector", description="Fraud detection model")

# Create a version from a run
client.create_model_version(
    name="fraud-detector",
    source="runs:/abc123/model",
    run_id="abc123",
    description="LightGBM with feature engineering v2"
)

# Promote to production via alias
client.set_registered_model_alias("fraud-detector", "champion", version=3)

# Load the champion model
model = mlflow.pyfunc.load_model("models:/fraud-detector@champion")
```

### Source Code Walkthrough

#### Run Entity -- The Atomic Unit of Tracking

The `Run` class is the core entity representing a single ML training execution. It composes `RunInfo` (metadata like ID, status, timing), `RunData` (parameters, metrics, tags), and optionally `RunInputs`/`RunOutputs`. The design uses composition over inheritance, making each component independently serializable via protobuf.

```python
# source: mlflow/entities/run.py:L1-L50
# github: mlflow/mlflow
# tag: v3.10.1
class Run(_MlflowObject):
    def __init__(self, run_info, run_data, run_inputs=None, run_outputs=None):
        if run_info is None:
            raise MlflowException("run_info cannot be None")
        self._info = run_info
        self._data = run_data
        self._inputs = run_inputs
        self._outputs = run_outputs

    @property
    def info(self):
        """The run metadata, such as the run id, start time, and status."""
        return self._info

    @property
    def data(self):
        """The run data, including metrics, parameters, and tags."""
        return self._data

    def to_dictionary(self):
        d = {"info": dict(self._info), "data": dict(self._data)}
        if self._inputs:
            d["inputs"] = dict(self._inputs)
        if self._outputs:
            d["outputs"] = dict(self._outputs)
        return d
```

The `_MlflowObject` base class provides `from_proto()` and `to_proto()` methods for gRPC serialization. Every entity in MLflow uses protobuf as its wire format -- this enables language-agnostic clients (Python, Java, R) to share the same server.

#### Experiment Entity -- The Organizational Container

The `Experiment` class manages experiment-level metadata including the artifact location, lifecycle stage (active/deleted), and trace configuration. Note how it handles backward compatibility with timestamp fields from older protocol versions.

```python
# source: mlflow/entities/experiment.py:L1-L60
# github: mlflow/mlflow
# tag: v3.10.1
class Experiment(_MlflowObject):
    def __init__(
        self, experiment_id, name, artifact_location, lifecycle_stage,
        tags=None, creation_time=None, last_update_time=None,
        workspace=None, trace_location=None,
    ):
        self._experiment_id = experiment_id
        self._name = name
        self._artifact_location = artifact_location
        self._lifecycle_stage = lifecycle_stage
        self._tags = {tag.key: tag.value for tag in (tags or [])}
        self._creation_time = creation_time
        self._last_update_time = last_update_time
        self._workspace = workspace
        self._trace_location = trace_location

    @property
    def experiment_id(self):
        return self._experiment_id

    @property
    def name(self):
        return self._name

    @property
    def artifact_location(self):
        """String root artifact URI for the experiment."""
        return self._artifact_location
```

The `artifact_location` property is critical -- it defines where all runs in this experiment store their artifacts. This supports per-experiment isolation: one experiment writes to `s3://bucket/team-a/`, another to `s3://bucket/team-b/`.

#### Fluent API -- Thread-Local Run Management

The fluent API functions in `tracking/fluent.py` are the primary interface most users interact with. Notice how `start_run` manages the global run stack and how `log_param` delegates to the active run.

```python
# source: mlflow/tracking/fluent.py:L200-L280
# github: mlflow/mlflow
# tag: v3.10.1
def start_run(
    run_id=None, experiment_id=None, run_name=None,
    nested=False, parent_run_id=None, tags=None,
    description=None, log_system_metrics=None,
):
    """Start a new MLflow run, setting it as the active run under which
    metrics and parameters will be logged."""
    # ... validation and client setup ...
    # Creates or resumes a run via the tracking client
    # Pushes the run onto the thread-local run stack
    # Returns an ActiveRun context manager

def log_param(key, value, synchronous=None):
    """Log a parameter (e.g. model hyperparameter) under the current run."""
    run_id = _get_or_start_run().info.run_id
    MlflowClient().log_param(run_id, key, value, synchronous=synchronous)

def log_metric(key, value, step=None, synchronous=None, timestamp=None,
               run_id=None, model_id=None, dataset=None):
    """Log a metric under the current run."""
    run_id = run_id or _get_or_start_run().info.run_id
    MlflowClient().log_metric(run_id, key, value, timestamp=timestamp,
                               step=step, synchronous=synchronous)
```

The `_get_or_start_run()` helper checks for an active run on the current thread's run stack. If none exists, it auto-creates one -- this is why you can call `mlflow.log_param()` without an explicit `start_run()` and it still works. The stack-based design supports nested runs (hyperparameter sweeps where each trial is a child run).

#### MlflowClient -- The Explicit API

The `MlflowClient` is the programmatic interface that wraps `TrackingServiceClient` and `ModelRegistryClient`. It provides explicit run ID management, avoiding the thread-local magic of the fluent API.

```python
# source: mlflow/tracking/client.py:L50-L120
# github: mlflow/mlflow
# tag: v3.10.1
class MlflowClient:
    """Client for an MLflow Tracking Server that creates and manages
    experiments and runs, and the Model Registry that creates and manages
    registered models and model versions."""

    def __init__(self, tracking_uri=None, registry_uri=None):
        # Resolves tracking URI from argument, env var, or default
        self._tracking_client = TrackingServiceClient(final_tracking_uri)
        self._registry_client = ModelRegistryClient(registry_uri)

    def log_param(self, run_id, key, value, synchronous=None):
        """Log a parameter against a given run."""
        self._tracking_client.log_param(run_id, key, value, synchronous=synchronous)

    def log_metric(self, run_id, key, value, timestamp=None, step=None,
                   synchronous=None, **kwargs):
        """Record a metric value against a run."""
        self._tracking_client.log_metric(run_id, key, value, timestamp, step,
                                          synchronous=synchronous, **kwargs)

    def create_experiment(self, name, artifact_location=None, tags=None):
        """Create an experiment. Returns the experiment ID."""
        return self._tracking_client.create_experiment(name, artifact_location, tags)

    def search_runs(self, experiment_ids, filter_string="", run_view_type=ViewType.ACTIVE_ONLY,
                    max_results=1000, order_by=None, page_token=None):
        """Search for runs matching criteria."""
        return self._tracking_client.search_runs(experiment_ids, filter_string,
                                                  run_view_type, max_results,
                                                  order_by, page_token)
```

The client constructor resolves the tracking URI using a well-defined precedence: explicit argument > `MLFLOW_TRACKING_URI` environment variable > default `./mlruns`. This three-level resolution means the same code works unchanged in development (local files), CI (remote server), and production (managed service).

#### SQLAlchemy Backend Store -- Where Metadata Lives

The `SqlAlchemyStore` is the production-grade backend store implementation. It manages all CRUD operations for experiments, runs, metrics, parameters, and tags using SQLAlchemy ORM.

```python
# source: mlflow/store/tracking/sqlalchemy_store.py:L50-L120
# github: mlflow/mlflow
# tag: v3.10.1
class SqlAlchemyStore(SqlAlchemyGatewayStoreMixin, AbstractStore):
    """SQLAlchemy-backed store for MLflow metadata tracking.
    Supports MySQL, MSSQL, SQLite, and PostgreSQL databases."""

    _engine_map = {}          # Class-level engine cache
    _engine_map_lock = threading.Lock()  # Thread-safe engine access

    def __init__(self, db_uri, default_artifact_root):
        self.db_uri = db_uri
        self.db_type = extract_db_type_from_uri(db_uri)
        self.engine = self._get_or_create_engine(db_uri)
        self._initialize_tables()
        self.ManagedSessionMaker = self._get_managed_session_maker()

    def log_metric(self, run_id, metric):
        """Log a metric with deduplication and latest-value tracking."""
        with self.ManagedSessionMaker() as session:
            run = self._get_run(session, run_id)
            # Sanitize NaN/Infinity values
            metric.value = sanitize_metric_value(metric.value)
            # Insert into full metrics history
            session.add(SqlMetric(run_uuid=run_id, **metric.to_dict()))
            # Update latest_metrics for fast queries
            self._update_latest_metric(session, run_id, metric)
```

Key design details: The class-level `_engine_map` with a lock prevents connection pool leaks when multiple `SqlAlchemyStore` instances are created (which happens frequently in long-running servers). The `ManagedSessionMaker` context manager provides automatic commit/rollback semantics. The dual-write to both `SqlMetric` (full history) and `SqlLatestMetric` (fast lookups) is an optimization -- queries like "find runs where accuracy > 0.9" only need to scan the latest metrics table.

#### Model Class -- The MLmodel Format

The `Model` class represents the MLmodel YAML file that accompanies every saved model. It defines the flavor system that enables framework-agnostic deployment.

```python
# source: mlflow/models/model.py:L80-L160
# github: mlflow/mlflow
# tag: v3.10.1
class Model:
    """An MLflow Model that can support multiple model flavors."""

    MLMODEL_FILE_NAME = "MLmodel"

    def __init__(self, artifact_path=None, run_id=None, utc_time_created=None,
                 flavors=None, signature=None, model_uuid=None, mlflow_version=None,
                 metadata=None, model_size_bytes=None, resources=None, **kwargs):
        self.artifact_path = artifact_path
        self.run_id = run_id
        self.flavors = flavors if flavors else {}
        self.signature = signature
        self.model_uuid = model_uuid or str(uuid.uuid4())
        self.mlflow_version = mlflow_version or mlflow.version.VERSION
        self.metadata = metadata

    def add_flavor(self, name, **params):
        """Add a flavor to the model. Each flavor defines how the model
        can be loaded and served by a specific framework."""
        self.flavors[name] = params
        return self

    def save(self, path):
        """Write the MLmodel file to the given directory."""
        with open(os.path.join(path, self.MLMODEL_FILE_NAME), "w") as f:
            self.to_yaml(f)

    @classmethod
    def load(cls, path):
        """Load an MLmodel from a directory or YAML file."""
        # Handles both directory paths and file paths
        # Returns a Model instance with all flavors and metadata
```

The `add_flavor` method is called by framework-specific `log_model` functions. For example, `mlflow.sklearn.log_model()` calls `model.add_flavor("sklearn", ...)` and `model.add_flavor("python_function", ...)`. The python_function flavor is always added -- it's the universal interface.

#### PyFuncModel -- The Universal Inference Interface

The `PyFuncModel` class wraps any MLflow model with a consistent `predict()` interface. This is what makes `mlflow models serve` work for any framework.

```python
# source: mlflow/pyfunc/__init__.py:L300-L380
# github: mlflow/mlflow
# tag: v3.10.1
class PyFuncModel:
    """Wrapper around model implementations and their metadata."""

    def __init__(self, model_meta, model_impl, predict_fn="predict",
                 predict_stream_fn=None, model_id=None):
        self._model_meta = model_meta
        self._model_impl = model_impl
        self._predict_fn = predict_fn

    def predict(self, data, params=None):
        """Generate predictions. Accepts pandas DataFrames, numpy arrays,
        scipy sparse matrices, Python lists/dicts, and Spark DataFrames."""
        predict_fn = getattr(self._model_impl, self._predict_fn)
        return predict_fn(data, params=params) if params else predict_fn(data)

    @property
    def metadata(self):
        """Model's configuration from the MLmodel file."""
        return self._model_meta

def load_model(model_uri, suppress_warnings=False, dst_path=None, model_config=None):
    """Load a model stored in MLflow format as a generic PyFuncModel.
    Downloads artifacts, validates flavor config, dynamically imports
    the loader module, and instantiates a PyFuncModel wrapper."""
    # Resolves model URI (runs:/..., models:/..., s3://...)
    # Downloads model artifacts to local path
    # Reads MLmodel file and extracts pyfunc flavor config
    # Dynamically imports the loader_module
    # Calls loader._load_pyfunc(path) to get the implementation
    # Wraps in PyFuncModel and returns
```

The `load_model` function is the deployment entry point. It resolves model URIs in several formats: `runs:/<run_id>/model` (from a specific run), `models:/<name>/<version>` (from the registry by version), `models:/<name>@<alias>` (from the registry by alias), or any artifact store path (`s3://...`). This URI system is what makes model references portable across environments.

#### Autologging Integration -- Safe Monkey-Patching

The autologging system uses a decorator-based approach to safely patch ML framework functions. The `autologging_integration` decorator registers integrations and manages their configuration.

```python
# source: mlflow/utils/autologging_utils/__init__.py:L100-L160
# github: mlflow/mlflow
# tag: v3.10.1
def autologging_integration(name):
    """Decorator that wraps an autologging function to store its
    configuration and enforce required parameters."""

    def wrapper(_autolog):
        param_spec = inspect.signature(_autolog).parameters
        validate_param_spec(param_spec)  # Must have 'disable' and 'silent'

        AUTOLOGGING_INTEGRATIONS[name] = {}

        @autologging_conf_lock  # Thread-safe configuration changes
        def autolog(*args, **kwargs):
            config_to_store = dict(default_params)
            config_to_store.update(resolved_args)
            AUTOLOGGING_INTEGRATIONS[name] = config_to_store
            # Revert any existing patches before applying new ones
            revert_patches(name)
            return _autolog(*args, **kwargs)

        wrapped_autolog.integration_name = name
        return wrapped_autolog
    return wrapper
```

The `revert_patches(name)` call before applying new patches is important -- it prevents patch stacking when autolog is called multiple times (e.g., re-running a notebook cell). The thread-safe lock ensures that concurrent calls to enable/disable autologging don't corrupt the global configuration state.

#### Model Registry Store -- Version Management

The model registry's SQLAlchemy store manages registered models and their versions with retry logic for concurrent version creation.

```python
# source: mlflow/store/model_registry/sqlalchemy_store.py:L60-L130
# github: mlflow/mlflow
# tag: v3.10.1
class SqlAlchemyStore(AbstractStore):
    """SQLAlchemy-backed model registry store."""

    def create_model_version(self, name, source, run_id=None, tags=None,
                             run_link=None, description=None, **kwargs):
        """Create a model version with retry logic for concurrent creation."""
        for attempt in range(CREATE_MODEL_VERSION_RETRIES):
            try:
                with self.ManagedSessionMaker() as session:
                    # Get next version number
                    version = self._get_next_version(session, name)
                    mv = SqlModelVersion(
                        name=name, version=version, source=source,
                        run_id=run_id, description=description
                    )
                    session.add(mv)
                    # Flush to detect concurrent version conflicts
                    session.flush()
                    return mv.to_mlflow_entity()
            except IntegrityError:
                if attempt < CREATE_MODEL_VERSION_RETRIES - 1:
                    continue
                raise

    def set_registered_model_alias(self, name, alias, version):
        """Assign an alias to a model version. Atomic operation."""
        with self.ManagedSessionMaker() as session:
            # Upsert: update existing alias or create new one
            self._upsert_alias(session, name, alias, version)
```

The retry loop on `create_model_version` handles the race condition where two users register a version simultaneously. Both compute the next version number, but only one INSERT succeeds -- the other gets an IntegrityError and retries with the updated version number. This optimistic concurrency pattern avoids locks while maintaining version uniqueness.

### Deployment Considerations

**Sizing:** The tracking server is lightweight -- a single instance handles thousands of concurrent training runs. For high availability, run multiple stateless instances behind a load balancer. Size the backend database based on your logging volume: a typical experiment with 100 runs, 50 metrics each logged at 100 steps generates about 500K metric rows.

**Monitoring:** MLflow exposes a `/health` endpoint for liveness checks. Monitor database connection pool usage, artifact store latency, and API response times. The `mlflow server --gunicorn-opts` flag lets you configure worker processes and threads for production deployments.

**Backup:** Back up the backend database using standard database tools (pg_dump for PostgreSQL). Artifact stores on S3/GCS have built-in durability. For the model registry, the database backup captures all model metadata -- the actual model files are in the artifact store.

**Security:** Enable authentication with `--app-name basic-auth` on the tracking server. For production, place the server behind a reverse proxy (nginx, Envoy) with TLS termination and integrate with your organization's identity provider. Use artifact store credentials (AWS IAM roles, GCP service accounts) to control who can access model files.

**Upgrades:** MLflow maintains backward compatibility for its REST API and database schema. Schema migrations run automatically on server startup via Alembic. Always back up your database before upgrading major versions. The client library is forward-compatible -- older clients can talk to newer servers.
