# Performance & Optimization

<!-- level:beginner -->
## Why FastAPI Is Fast

FastAPI earns its name. It is one of the fastest Python web frameworks available. But understanding *why* requires looking at a few layers.

### The Speed Stack

FastAPI's performance comes from the libraries it builds on:

```
Your FastAPI App
      |
      v
  Pydantic V2 (validation written in Rust via pydantic-core)
      |
      v
  Starlette (lightweight ASGI framework)
      |
      v
  Uvicorn (ASGI server using uvloop and httptools, both written in C)
      |
      v
  Operating System (epoll/kqueue for async I/O)
```

Each layer is optimized:
- **uvloop** replaces Python's default `asyncio` event loop with a C implementation (2-4x faster)
- **httptools** is a C-based HTTP parser (replaces Python's h11)
- **pydantic-core** is a Rust library for validation (5-50x faster than Pydantic V1)
- **Starlette** is a minimal ASGI framework with very little overhead

### Benchmark Numbers

Based on TechEmpower and community benchmarks (2025):

| Framework | Requests/second (JSON serialization) |
|---|---|
| Uvicorn (raw ASGI) | ~30,000 |
| Starlette | ~25,000 |
| **FastAPI** | ~15,000-20,000 |
| Sanic | ~12,000 |
| Django REST Framework | ~2,000-3,000 |
| Flask | ~2,000-4,000 |

FastAPI is slightly slower than raw Starlette because it adds validation and dependency injection overhead. But this overhead is small and buys you a lot of functionality.

### Async vs Sync: When It Matters

The performance advantage of async is most visible with I/O-bound workloads:

```python
# Scenario: Endpoint calls 3 external APIs

# Synchronous (Flask-style): ~3 seconds total
def get_dashboard():
    user = requests.get("http://user-service/user/1")        # 1 second
    orders = requests.get("http://order-service/orders")      # 1 second
    notifications = requests.get("http://notif-service/new")  # 1 second
    return combine(user, orders, notifications)

# Asynchronous (FastAPI): ~1 second total
async def get_dashboard():
    async with httpx.AsyncClient() as client:
        user, orders, notifications = await asyncio.gather(
            client.get("http://user-service/user/1"),        # \
            client.get("http://order-service/orders"),        #  } all at once
            client.get("http://notif-service/new"),           # /
        )
    return combine(user, orders, notifications)
```

The async version is 3x faster because it runs all three HTTP calls concurrently on a single thread.

<!-- level:intermediate -->
## Optimization Techniques

### 1. Use Async Where It Matters

Not everything needs to be async. The rule is simple:

| Scenario | Use | Why |
|---|---|---|
| Calling async DB driver (asyncpg) | `async def` | Native async support |
| Calling sync DB driver (psycopg2) | `def` | Let FastAPI thread-pool it |
| Multiple concurrent HTTP calls | `async def` + `gather` | Parallel I/O |
| CPU-heavy computation | `def` (or offload) | Don't block the loop |
| Simple in-memory operation | Either | Doesn't matter |

### 2. Response Model Optimization

Use `response_model_exclude_unset` to avoid serializing fields that were never set:

```python
@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    return get_item_from_db(item_id)

# Faster: skip None fields in response
@app.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    response_model_exclude_unset=True,
)
def get_item_fast(item_id: int):
    return get_item_from_db(item_id)
```

For maximum performance, bypass Pydantic serialization entirely:

```python
from fastapi.responses import ORJSONResponse

app = FastAPI(default_response_class=ORJSONResponse)

# Or per-route:
@app.get("/fast-items/", response_class=ORJSONResponse)
def get_items():
    return [{"id": 1, "name": "Widget"}]
```

`orjson` is a fast JSON serializer written in Rust, significantly faster than Python's built-in `json` module.

### 3. Database Connection Pooling

Always configure connection pools properly:

```python
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=20,          # Base pool size
    max_overflow=10,       # Extra connections when pool is full
    pool_timeout=30,       # Seconds to wait for a connection
    pool_recycle=1800,     # Recycle connections after 30 minutes
    pool_pre_ping=True,    # Verify connections are alive
)
```

### 4. Caching Strategies

**Response caching**:
```python
from fastapi_cache.decorator import cache

@app.get("/products/")
@cache(expire=60)
async def list_products():
    return await expensive_db_query()
```

**Computed property caching** (avoid recomputing on every request):
```python
from functools import lru_cache

@lru_cache
def get_settings():
    return Settings()  # Read from env once, cache forever
```

### 5. Pagination (Never Return Everything)

```python
@app.get("/items/")
async def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: DbSession = Depends(),
):
    # Always limit database queries
    items = await db.scalars(
        select(Item).offset(skip).limit(limit)
    )
    return items.all()
```

### 6. Gzip Compression

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

This compresses responses larger than 1000 bytes, reducing bandwidth significantly for JSON APIs.

<!-- level:advanced -->
## Deep Performance Analysis

### Event Loop Monitoring

The most common performance problem in FastAPI applications is accidentally blocking the event loop. Here is how to detect it:

```python
import asyncio
import time
import logging

logger = logging.getLogger("slowloop")

class EventLoopMonitor:
    """Detect when the event loop is blocked for too long."""

    def __init__(self, threshold_ms: float = 100):
        self.threshold = threshold_ms / 1000
        self._task = None

    async def start(self):
        self._task = asyncio.create_task(self._monitor())

    async def _monitor(self):
        while True:
            start = time.monotonic()
            await asyncio.sleep(0.1)
            elapsed = time.monotonic() - start
            delay = elapsed - 0.1
            if delay > self.threshold:
                logger.warning(
                    f"Event loop was blocked for {delay*1000:.0f}ms "
                    f"(threshold: {self.threshold*1000:.0f}ms)"
                )

# Use in lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    monitor = EventLoopMonitor(threshold_ms=100)
    await monitor.start()
    yield
```

### Profiling FastAPI Applications

**Using pyinstrument**:
```python
from pyinstrument import Profiler
from fastapi import Request

@app.middleware("http")
async def profile_request(request: Request, call_next):
    if request.query_params.get("profile"):
        profiler = Profiler(async_mode="enabled")
        profiler.start()
        response = await call_next(request)
        profiler.stop()
        # Log or return profiler output
        print(profiler.output_text(unicode=True, color=True))
        return response
    return await call_next(request)
```

### Worker Configuration Tuning

**Single-server deployment (Gunicorn + Uvicorn)**:

```python
# gunicorn.conf.py
import multiprocessing

# Workers = CPU cores * 2 + 1 (classic formula)
# For I/O-heavy apps, increase; for CPU-heavy, match CPU count
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Connection handling
worker_connections = 1000  # Per-worker concurrent connections
backlog = 2048             # Pending connection queue
timeout = 120              # Worker timeout (restart if stuck)
graceful_timeout = 30      # Time for graceful shutdown
keepalive = 5              # Keep-alive timeout

# Memory management
max_requests = 10000       # Restart workers after N requests (prevents memory leaks)
max_requests_jitter = 1000 # Randomize restart to avoid thundering herd
```

**Kubernetes deployment (single worker per pod)**:

```bash
# Let K8s handle scaling; use one worker per pod
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --loop uvloop --http httptools
```

### Understanding the Overhead

FastAPI adds overhead compared to raw Starlette. Here is what costs time:

| Operation | Approximate Cost | Notes |
|---|---|---|
| Dependency resolution | 5-50 microseconds | Per-request DI graph walk |
| Pydantic validation | 10-100 microseconds | Depends on model complexity |
| Response serialization | 5-50 microseconds | Pydantic V2 is very fast |
| OpenAPI schema gen | 0 (cached) | Generated once, served from cache |
| Middleware stack | 1-5 microseconds per layer | Depends on middleware logic |

For most applications, this overhead is negligible compared to network I/O and database queries.

### Pydantic V2 Performance Characteristics

Pydantic V2's Rust core (pydantic-core) provides massive speedups:

```
Benchmark: Validate 1000 complex nested objects

Pydantic V1:  ~120ms
Pydantic V2:  ~3ms (40x faster)

Benchmark: Serialize 1000 objects to JSON

Pydantic V1 + json.dumps:  ~80ms
Pydantic V2 .model_dump_json():  ~2ms (40x faster)
```

To maximize Pydantic V2 performance:
- Use `model_validate()` instead of `__init__()` when parsing external data
- Use `model_dump_json()` instead of `json.dumps(model.model_dump())`
- Enable strict mode when you don't need type coercion
- Use `TypeAdapter` for validating non-model types

### ORJSONResponse vs JSONResponse

```python
import orjson
from fastapi.responses import ORJSONResponse

# Default JSONResponse uses Python's json module
# ORJSONResponse uses orjson (written in Rust)

# Benchmark: Serialize a large list of dicts
# json.dumps:  ~15ms for 10,000 items
# orjson.dumps: ~2ms for 10,000 items (7.5x faster)

app = FastAPI(default_response_class=ORJSONResponse)
```

Install with: `pip install orjson`

### Connection Pool Exhaustion

A common production issue is running out of database connections:

```python
# Symptom: requests hang, then timeout with "connection pool exhausted"

# Prevention: monitor pool stats
from sqlalchemy import event

@event.listens_for(engine.sync_engine, "checkout")
def log_checkout(dbapi_conn, connection_record, connection_proxy):
    pool = engine.sync_engine.pool
    logger.debug(
        f"Pool status: size={pool.size()}, "
        f"checked_out={pool.checkedout()}, "
        f"overflow={pool.overflow()}"
    )

# Fix: ensure connections are always returned
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()  # Always return to pool
```

### When FastAPI Is Not Fast Enough

If you hit Python's performance ceiling:

1. **Profile first**: Is the bottleneck in your code, the framework, or I/O?
2. **Offload CPU work**: Use Celery/Dramatiq for heavy computation
3. **Cache aggressively**: Redis caching for repeated queries
4. **Use streaming**: `StreamingResponse` for large payloads instead of buffering
5. **Consider a hybrid**: Write performance-critical paths in Go/Rust, keep the rest in FastAPI
6. **Optimize the database**: Most "slow API" problems are actually slow queries
