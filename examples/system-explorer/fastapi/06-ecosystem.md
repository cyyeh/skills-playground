# Ecosystem & Integrations

<!-- level:beginner -->
## The FastAPI Ecosystem

FastAPI benefits from a rich ecosystem of compatible libraries. Because it is built on standard Python tools (Pydantic, Starlette, ASGI), it integrates naturally with most of the Python ecosystem.

### Core Dependencies

These are installed automatically with `pip install "fastapi[standard]"`:

| Package | Purpose |
|---|---|
| **Starlette** | Web framework foundation |
| **Pydantic** | Data validation and settings |
| **Uvicorn** | ASGI server |
| **httpx** | HTTP client (for testing and API calls) |
| **Jinja2** | Template engine for HTML |
| **python-multipart** | Form data and file upload parsing |
| **email-validator** | Email field validation |
| **fastapi-cli** | `fastapi dev` and `fastapi run` commands |

### Database Libraries

FastAPI works with any Python database library. The most popular choices:

**SQLAlchemy** (most popular ORM):
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
```

**SQLModel** (by the same author as FastAPI):
```python
from sqlmodel import SQLModel, Field

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: int | None = None
```

SQLModel combines SQLAlchemy and Pydantic into a single model, so the same class works as both a database model and an API schema.

**Other database options**:
- **Tortoise ORM** -- Django-style async ORM
- **Piccolo** -- Async ORM with built-in migrations
- **Beanie** -- MongoDB ODM built on Pydantic
- **Motor** -- Async MongoDB driver
- **Databases** -- Async database support for SQLAlchemy core

### Authentication Libraries

- **python-jose** -- JWT token encoding/decoding
- **passlib** -- Password hashing (bcrypt, argon2)
- **authlib** -- OAuth 1/2 client and server
- **fastapi-users** -- Full user management (registration, login, password reset)

### API Documentation

FastAPI auto-generates documentation, but you can customize it:

```python
app = FastAPI(
    title="My API",
    description="A comprehensive API for managing widgets",
    version="2.0.0",
    docs_url="/docs",          # Swagger UI path
    redoc_url="/redoc",        # ReDoc path
    openapi_url="/openapi.json",  # OpenAPI schema path
)
```

<!-- level:intermediate -->
## Integration Patterns

### Async Database Stack (SQLAlchemy + Alembic)

The most common production database setup:

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/mydb"

engine = create_async_engine(DATABASE_URL, pool_size=20, max_overflow=10)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass
```

Database migrations with Alembic:

```bash
# Initialize Alembic
alembic init alembic

# Configure alembic/env.py for async
# Generate migration
alembic revision --autogenerate -m "add users table"

# Apply migrations
alembic upgrade head
```

```python
# alembic/env.py (async configuration)
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import Base, DATABASE_URL

def run_migrations_online():
    connectable = create_async_engine(DATABASE_URL)

    async def do_run_migrations(connection):
        await connection.run_sync(do_migrations)

    async def run_async():
        async with connectable.connect() as connection:
            await do_run_migrations(connection)

    asyncio.run(run_async())
```

### Task Queues

For CPU-intensive or long-running work, use a task queue:

**Celery** (most popular):
```python
from celery import Celery
from fastapi import FastAPI, BackgroundTasks

celery_app = Celery("tasks", broker="redis://localhost:6379")

@celery_app.task
def process_report(report_id: int):
    # CPU-intensive work runs in Celery worker
    generate_pdf(report_id)
    send_email_notification(report_id)

@app.post("/reports/")
async def create_report(report: ReportCreate, db: DbSession):
    db_report = await save_report(db, report)
    process_report.delay(db_report.id)  # Queue for background processing
    return {"id": db_report.id, "status": "processing"}
```

**Dramatiq** (simpler alternative):
```python
import dramatiq
from dramatiq.brokers.redis import RedisBroker

broker = RedisBroker(url="redis://localhost:6379")
dramatiq.set_broker(broker)

@dramatiq.actor
def send_welcome_email(user_id: int):
    user = get_user(user_id)
    send_email(user.email, "Welcome!", "...")

@app.post("/users/")
async def create_user(user: UserCreate):
    new_user = await save_user(user)
    send_welcome_email.send(new_user.id)
    return new_user
```

### Caching

**Redis caching with fastapi-cache2**:
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="api-cache")
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/expensive-data/")
@cache(expire=300)  # Cache for 5 minutes
async def get_expensive_data():
    return await compute_expensive_result()
```

### Monitoring and Observability

**OpenTelemetry integration**:
```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Set up tracing
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)

# Instrument FastAPI (one line!)
FastAPIInstrumentor.instrument_app(app)
```

**Prometheus metrics**:
```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
# Metrics available at /metrics
```

### GraphQL Integration

FastAPI can serve GraphQL alongside REST:

```python
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
import strawberry

@strawberry.type
class Book:
    title: str
    author: str

@strawberry.type
class Query:
    @strawberry.field
    def books(self) -> list[Book]:
        return [Book(title="1984", author="Orwell")]

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

<!-- level:advanced -->
## Advanced Ecosystem Patterns

### Custom ASGI Middleware

When Starlette's `BaseHTTPMiddleware` is insufficient (e.g., for WebSocket handling or streaming), write pure ASGI middleware:

```python
class RawASGIMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Intercept response to add headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append([b"x-custom", b"value"])
                    message["headers"] = headers
                await send(message)
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

app.add_middleware(RawASGIMiddleware)
```

Note: `BaseHTTPMiddleware` buffers the entire response body, which breaks streaming responses. For streaming endpoints, use pure ASGI middleware or Starlette's newer `ASGIMiddleware` pattern.

### Multi-Application Mounting

FastAPI supports mounting multiple ASGI applications under one umbrella:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Main API
api_app = FastAPI(title="Main API")

# Admin API (separate OpenAPI schema)
admin_app = FastAPI(title="Admin API")

# Combined application
main_app = FastAPI()
main_app.mount("/api", api_app)
main_app.mount("/admin", admin_app)
main_app.mount("/static", StaticFiles(directory="static"), name="static")

# Each mounted app has its own /docs
# /api/docs -- API documentation
# /admin/docs -- Admin documentation
```

### Plugin Architecture

Build extensible FastAPI applications with a plugin system:

```python
from importlib import import_module
from pathlib import Path
from fastapi import FastAPI, APIRouter

def discover_plugins(plugin_dir: str = "plugins") -> list[APIRouter]:
    routers = []
    plugin_path = Path(plugin_dir)
    for plugin_file in plugin_path.glob("*/router.py"):
        module_path = str(plugin_file).replace("/", ".").removesuffix(".py")
        module = import_module(module_path)
        if hasattr(module, "router"):
            routers.append(module.router)
    return routers

app = FastAPI()

# Auto-discover and register plugins
for router in discover_plugins():
    app.include_router(router)
```

### Awesome FastAPI Libraries

A curated selection of battle-tested ecosystem libraries:

| Library | Purpose | Notes |
|---|---|---|
| **SQLModel** | ORM combining SQLAlchemy + Pydantic | Same author as FastAPI |
| **fastapi-users** | Complete user management | Registration, login, OAuth |
| **fastapi-cache2** | Response caching | Redis/Memcached backends |
| **fastapi-limiter** | Rate limiting | Redis-based |
| **fastapi-pagination** | Automatic pagination | Multiple pagination styles |
| **fastapi-mail** | Email sending | SMTP, templates |
| **slowapi** | Rate limiting | Based on Flask-Limiter |
| **fastapi-cors** | CORS handling | Built into Starlette |
| **Strawberry** | GraphQL | Type-safe, FastAPI integration |
| **Beanie** | MongoDB ODM | Pydantic-native |
| **Ormar** | Async ORM | Pydantic models as DB models |
| **FastSQLA** | SQLAlchemy extension | Pagination, async support |
| **prometheus-fastapi-instrumentator** | Metrics | Prometheus integration |
| **opentelemetry-instrumentation-fastapi** | Tracing | OpenTelemetry integration |

### FastAPI Cloud

The creator of FastAPI launched FastAPI Cloud, a managed deployment platform. While not required (FastAPI deploys anywhere), it offers:
- Zero-config deployment from GitHub
- Automatic HTTPS
- Managed database connections
- Built-in monitoring
- Auto-scaling

This is a commercial offering and entirely optional. FastAPI itself remains MIT-licensed and deploys on any platform that runs Python.
