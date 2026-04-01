# Architecture & Internals

<!-- level:beginner -->
## How FastAPI Is Built

FastAPI is not a framework written from scratch. It is a carefully composed layer on top of two powerful libraries. Understanding this architecture helps you understand what FastAPI does itself versus what it delegates.

### The Layer Cake

```
+--------------------------------------------------+
|                  Your Application                 |
|   (path operations, models, business logic)       |
+--------------------------------------------------+
|                    FastAPI                         |
|   (routing wrappers, DI, security, OpenAPI gen)   |
+--------------------------------------------------+
|                   Starlette                        |
|   (ASGI framework: routing, middleware, etc.)      |
+--------------------------------------------------+
|                   Pydantic                         |
|   (data validation, serialization, JSON Schema)   |
+--------------------------------------------------+
|              ASGI Server (Uvicorn)                 |
|   (event loop, HTTP parsing, connection mgmt)     |
+--------------------------------------------------+
```

**Starlette** handles everything about receiving and sending HTTP (and WebSocket) data. It is the web server interface layer.

**Pydantic** handles everything about data -- parsing JSON, validating types, converting formats, and generating schemas.

**FastAPI** is the glue that connects your Python functions (with their type hints) to Starlette's routing and Pydantic's validation, and then generates OpenAPI documentation from the result.

### What Is ASGI?

ASGI stands for **Asynchronous Server Gateway Interface**. It is the successor to WSGI (used by Flask and Django).

Think of ASGI as a contract between the web server and your application:

- **WSGI** (old): The server sends a request, your app returns a response. One request at a time per worker.
- **ASGI** (new): The server and your app communicate asynchronously. A single worker can handle thousands of concurrent connections.

```
WSGI (Flask/Django default):
  Request --> [Worker 1] --> Response
  Request --> [Worker 2] --> Response  (need more workers for more concurrency)

ASGI (FastAPI):
  Request 1 --|
  Request 2 --|---> [Single Worker with Event Loop] ---> Responses
  Request 3 --|     (handles all concurrently)
```

### How a Request Flows

1. A client sends an HTTP request (e.g., `GET /items/42?q=search`)
2. **Uvicorn** receives the raw bytes, parses HTTP, creates an ASGI scope
3. **Starlette** matches the URL to a route via its router
4. **FastAPI** resolves dependencies, validates parameters using Pydantic
5. Your **path operation function** runs with validated, typed arguments
6. FastAPI serializes your return value to JSON
7. The response flows back through middleware and out to the client

<!-- level:intermediate -->
## Starlette Foundation

Since `FastAPI` inherits from `Starlette`, you have access to all Starlette features. Understanding what lives at the Starlette layer versus the FastAPI layer helps you debug issues and know where to look in documentation.

### What Starlette Provides

| Feature | Starlette Layer | FastAPI Adds |
|---|---|---|
| URL routing | Basic path matching | Type-validated path params |
| Request/Response objects | `Request`, `Response` classes | Pydantic-based parsing |
| Middleware | Full ASGI middleware support | Built-in CORS, etc. |
| WebSockets | WebSocket connections | Typed WebSocket handlers |
| Background tasks | `BackgroundTask` class | `BackgroundTasks` DI |
| Static files | `StaticFiles` mount | Same (inherited) |
| Test client | `TestClient` (httpx) | Same + DI overrides |
| Lifespan events | `lifespan` context manager | Same (inherited) |
| ASGI sub-apps | `Mount` for sub-applications | `APIRouter` + Mount |

### The Router System

FastAPI uses an extended version of Starlette's router:

```python
from fastapi import FastAPI, APIRouter

# Main application
app = FastAPI()

# Sub-routers for organization
users_router = APIRouter(prefix="/users", tags=["users"])
items_router = APIRouter(prefix="/items", tags=["items"])

@users_router.get("/")
def list_users():
    return [{"id": 1, "name": "Alice"}]

@items_router.get("/")
def list_items():
    return [{"id": 1, "name": "Widget"}]

# Include routers in the app
app.include_router(users_router)
app.include_router(items_router)
```

`APIRouter` is FastAPI's extension of Starlette's `Router`. It adds:
- Dependency injection support
- Response model declarations
- OpenAPI metadata (tags, descriptions)
- Prefix-based URL grouping

### Middleware Architecture

Middleware in FastAPI/Starlette wraps the entire request-response cycle:

```python
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import time

app = FastAPI()

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        return response

app.add_middleware(TimingMiddleware)
```

Middleware execution order forms a stack -- the last middleware added is the outermost:

```
Request  -->  Middleware C  -->  Middleware B  -->  Middleware A  -->  Route
Response <--  Middleware C  <--  Middleware B  <--  Middleware A  <--  Route
```

### Pydantic Integration Architecture

FastAPI uses Pydantic at multiple levels:

1. **Request body parsing**: JSON body --> Pydantic model instance
2. **Query/path/header validation**: Raw strings --> typed Python values
3. **Response serialization**: Python objects --> JSON (filtered by response_model)
4. **OpenAPI generation**: Pydantic models --> JSON Schema --> OpenAPI spec

```python
from pydantic import BaseModel, Field

class ItemCreate(BaseModel):
    """This docstring becomes the schema description in OpenAPI."""
    name: str = Field(..., min_length=1, max_length=100, examples=["Widget"])
    price: float = Field(..., gt=0, description="Price in USD")
    tags: list[str] = Field(default_factory=list)

class ItemResponse(ItemCreate):
    id: int
    created_at: datetime
```

<!-- level:advanced -->
## Internals Deep Dive

### ASGI Protocol Details

At the lowest level, FastAPI is an ASGI application. The ASGI spec defines three types of communication:

```python
# The core ASGI interface (simplified)
async def app(scope, receive, send):
    """
    scope: dict with connection info (type, path, headers, etc.)
    receive: async callable to get incoming messages
    send: async callable to send outgoing messages
    """
    if scope["type"] == "http":
        # Handle HTTP request
        body = await receive()  # {"type": "http.request", "body": b"..."}
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"hello": "world"}',
        })
    elif scope["type"] == "websocket":
        # Handle WebSocket connection
        ...
    elif scope["type"] == "lifespan":
        # Handle startup/shutdown
        ...
```

Starlette abstracts this into `Request` and `Response` objects. FastAPI further abstracts it into typed function parameters. But the raw ASGI interface is always accessible when you need it.

### Dependency Injection Internals

FastAPI's DI system builds a directed acyclic graph (DAG) of dependencies at startup. At request time, it performs a topological sort to resolve them in the correct order.

```
          get_current_user
           /            \
    get_token        get_db_session
        |                |
    OAuth2Scheme     SessionLocal
```

Key implementation details:

1. **Per-request caching**: If the same dependency appears multiple times in the graph, it is called only once per request. The result is reused.

2. **Yield-based lifecycle**: Dependencies using `yield` create a context manager pattern:

```python
async def get_db():
    db = SessionLocal()
    try:
        yield db          # <-- value injected into handler
    finally:
        await db.close()  # <-- runs after response is sent
```

3. **Resolution order**: Dependencies with `yield` have their teardown code run after the response is sent but before background tasks execute. The full order is:

```
1. Resolve dependencies (depth-first)
2. Run path operation function
3. Send response
4. Run dependency teardown (yield cleanup)
5. Run background tasks
```

4. **Thread pool for sync dependencies**: If a dependency is a regular `def` (not `async def`), FastAPI runs it in a thread pool via `anyio.to_thread.run_sync()`. This prevents blocking the event loop.

### How OpenAPI Schema Generation Works

FastAPI generates the OpenAPI schema lazily (on first request to `/openapi.json`):

1. **Route scanning**: Iterates through all registered routes (including sub-routers)
2. **Parameter extraction**: For each route, inspects the function signature to extract path params, query params, headers, cookies, and body models
3. **Schema building**: Converts Pydantic models to JSON Schema using `model.model_json_schema()`
4. **Dependency documentation**: Dependencies that declare parameters (e.g., security schemes) contribute to the schema
5. **Caching**: The schema is computed once and cached; subsequent requests serve the cached version

```python
# You can access and customize the schema
@app.get("/openapi.json", include_in_schema=False)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        routes=app.routes,
    )
    # Customize schema here
    app.openapi_schema = openapi_schema
    return app.openapi_schema
```

### Event Loop and Concurrency Model

FastAPI runs on a single-threaded event loop (via `asyncio` / `uvloop`):

```
Main Thread (Event Loop):
  |-- async handler 1 (awaiting DB) -----> resumes ---> sends response
  |-- async handler 2 (awaiting HTTP) ---> resumes ---> sends response
  |-- async handler 3 (computing) -------> sends response
  |
  |-- Thread Pool:
       |-- sync handler 4 (blocking I/O) -> sends response
       |-- sync handler 5 (CPU work) -----> sends response
```

- `async def` handlers run directly on the event loop. They must not block.
- Regular `def` handlers run in a thread pool (default: 40 threads via AnyIO).
- CPU-intensive work in async handlers blocks the entire event loop. Use `run_in_executor` or a task queue for heavy computation.

### Starlette's ServerErrorMiddleware

By default, Starlette wraps the entire application in `ServerErrorMiddleware`. If any exception escapes all other handlers:
- In debug mode: returns an HTML traceback page
- In production mode: returns a plain 500 Internal Server Error

FastAPI adds `ExceptionMiddleware` on top, which handles `HTTPException` and `RequestValidationError` to return structured JSON error responses.

### Memory and Startup Characteristics

FastAPI applications have specific startup characteristics worth understanding:

- **Route compilation** happens at `app = FastAPI()` time and during `include_router()` calls. Each route's dependency graph is analyzed and compiled.
- **OpenAPI schema** is generated lazily on first access to `/docs` or `/openapi.json`.
- **Pydantic model compilation** (V2) happens at class definition time. Models with complex validators may have a noticeable import-time cost.
- **No global mutable state by default**: FastAPI encourages stateless handlers with dependency injection, making it naturally suited for multi-process deployments.
