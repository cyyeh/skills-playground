# Getting Started

<!-- level:beginner -->
## Installation and First Steps

### Prerequisites

- Python 3.8 or later (3.11+ recommended for best performance)
- A code editor with Python support (VS Code, PyCharm, etc.)
- Basic familiarity with Python

### Installation

The recommended installation includes standard dependencies:

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install FastAPI with all standard extras
pip install "fastapi[standard]"
```

This installs FastAPI along with:
- **uvicorn** -- ASGI server to run your app
- **httpx** -- HTTP client (used for testing)
- **jinja2** -- Template engine (for HTML responses)
- **python-multipart** -- Form and file upload parsing
- **email-validator** -- Email validation for Pydantic
- **fastapi-cli** -- Command-line tool for development

### Your First API

Create a file called `main.py`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello, World!"}

@app.get("/greet/{name}")
def greet(name: str):
    return {"message": f"Hello, {name}!"}
```

### Running the Application

```bash
# Development mode (auto-reload on code changes)
fastapi dev main.py

# Or using uvicorn directly
uvicorn main:app --reload
```

Your API is now running at `http://127.0.0.1:8000`.

### Exploring Your API

Open a browser and visit:
- `http://127.0.0.1:8000/` -- Your root endpoint
- `http://127.0.0.1:8000/greet/Alice` -- Greeting with a name
- `http://127.0.0.1:8000/docs` -- Interactive Swagger UI documentation
- `http://127.0.0.1:8000/redoc` -- Alternative ReDoc documentation

The Swagger UI at `/docs` lets you try out every endpoint interactively -- click "Try it out", fill in parameters, and execute requests right from the browser.

### Adding Request Bodies

For POST/PUT/PATCH requests, define a Pydantic model:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Todo(BaseModel):
    title: str
    completed: bool = False

todos: list[Todo] = []

@app.post("/todos/")
def create_todo(todo: Todo):
    todos.append(todo)
    return {"message": "Todo created", "todo": todo}

@app.get("/todos/")
def list_todos():
    return todos
```

Test it with curl:

```bash
# Create a todo
curl -X POST http://127.0.0.1:8000/todos/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn FastAPI", "completed": false}'

# List all todos
curl http://127.0.0.1:8000/todos/
```

### Query Parameters

Parameters not in the URL path are automatically treated as query parameters:

```python
@app.get("/items/")
def list_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}
```

Call with: `GET /items/?skip=20&limit=50`

<!-- level:intermediate -->
## Building a Real Application

### Project Structure

A typical FastAPI project looks like this:

```
my_project/
    app/
        __init__.py
        main.py          # FastAPI app instance, include routers
        config.py         # Settings and configuration
        database.py       # Database connection setup
        models/           # Pydantic models (schemas)
            __init__.py
            user.py
            item.py
        routers/          # API route handlers
            __init__.py
            users.py
            items.py
        services/         # Business logic
            __init__.py
            user_service.py
        dependencies.py   # Shared dependencies
    tests/
        __init__.py
        test_users.py
        test_items.py
    alembic/              # Database migrations
    pyproject.toml
```

### Main Application File

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import users, items
from app.database import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize resources
    print("Starting up...")
    yield
    # Shutdown: clean up resources
    print("Shutting down...")
    await engine.dispose()

app = FastAPI(
    title="My API",
    description="A well-structured FastAPI application",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(users.router)
app.include_router(items.router)
```

### Router Module

```python
# app/routers/users.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import UserCreate, UserResponse
from app.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )
    return await create_db_user(db, user)

@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
):
    return await get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### Configuration with Pydantic Settings

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "My API"
    debug: bool = False
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 30

    model_config = {"env_file": ".env"}

settings = Settings()
```

This reads configuration from environment variables (or a `.env` file), with full type validation.

### Database Setup (Async SQLAlchemy)

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Writing Tests

```python
# tests/test_users.py
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

@pytest.mark.anyio
async def test_create_user(client: AsyncClient):
    response = await client.post(
        "/users/",
        json={"username": "alice", "email": "alice@example.com", "password": "secret"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "alice"
    assert "password" not in data  # Filtered by response_model

@pytest.mark.anyio
async def test_get_nonexistent_user(client: AsyncClient):
    response = await client.get("/users/99999")
    assert response.status_code == 404
```

<!-- level:advanced -->
## Production-Ready Setup

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY app/ app/

# Run with uvicorn
# In Kubernetes: use single worker (scale with pods)
# On a single server: use multiple workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Kubernetes Deployment

When deploying to Kubernetes, use a single Uvicorn worker per pod and let Kubernetes handle scaling:

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
      - name: fastapi
        image: my-registry/fastapi-app:latest
        ports:
        - containerPort: 8000
        command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 20
```

### Health Check Endpoint

```python
from fastapi import FastAPI
from sqlalchemy import text

app = FastAPI()

@app.get("/health")
async def health_check():
    """Liveness check -- is the process alive?"""
    return {"status": "ok"}

@app.get("/ready")
async def readiness_check(db=Depends(get_db)):
    """Readiness check -- can we serve traffic?"""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database not ready")
```

### Structured Logging

```python
import logging
import structlog
from fastapi import FastAPI, Request

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    log = logger.bind(
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown",
    )
    log.info("request_started")
    response = await call_next(request)
    log.info("request_completed", status_code=response.status_code)
    return response
```

### Gunicorn + Uvicorn (Single Server Deployment)

```bash
# gunicorn.conf.py
import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
```

```bash
gunicorn app.main:app -c gunicorn.conf.py
```

This runs Gunicorn as the process manager with Uvicorn workers. Gunicorn handles worker lifecycle (restart on crash, graceful shutdown), while Uvicorn handles async request processing.

### Reverse Proxy with Nginx

```nginx
upstream fastapi {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_for_addr;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```
