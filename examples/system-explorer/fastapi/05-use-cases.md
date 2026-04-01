# Use Cases & Adoption

<!-- level:beginner -->
## What Is FastAPI Good For?

FastAPI is designed specifically for building APIs -- the backend services that power modern applications. Here are the most common use cases:

### REST APIs

The bread and butter of FastAPI. If you need to build a JSON API that mobile apps, web frontends, or other services consume, FastAPI is an excellent choice.

```python
# A typical REST API for a blog
@app.get("/posts/")
def list_posts(category: str | None = None):
    ...

@app.post("/posts/")
def create_post(post: PostCreate, user: CurrentUser):
    ...

@app.get("/posts/{post_id}")
def get_post(post_id: int):
    ...
```

### Microservices

FastAPI's lightweight nature and fast startup time make it ideal for microservices. Each service can be a small FastAPI application with its own API.

### Machine Learning Model Serving

FastAPI has become the de facto standard for serving ML models. Its async support handles concurrent prediction requests efficiently, and Pydantic models naturally describe the input/output shapes of ML models.

```python
from fastapi import FastAPI
from pydantic import BaseModel
import joblib

app = FastAPI()
model = joblib.load("model.pkl")

class PredictionInput(BaseModel):
    feature_1: float
    feature_2: float
    feature_3: float

class PredictionOutput(BaseModel):
    prediction: float
    confidence: float

@app.post("/predict", response_model=PredictionOutput)
def predict(data: PredictionInput):
    features = [[data.feature_1, data.feature_2, data.feature_3]]
    prediction = model.predict(features)[0]
    confidence = model.predict_proba(features).max()
    return PredictionOutput(prediction=prediction, confidence=confidence)
```

### Internal Tools and Admin APIs

Companies often build internal APIs for operations, data management, and tooling. FastAPI's automatic documentation makes these APIs self-documenting, reducing the need for separate docs.

### Webhook Receivers

FastAPI is well-suited for receiving webhooks from third-party services (Stripe, GitHub, Slack, etc.) because of its built-in request validation.

```python
@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    if event["type"] == "payment_intent.succeeded":
        await handle_payment_success(event["data"]["object"])
    return {"status": "ok"}
```

### Who Uses FastAPI?

| Company | Use Case |
|---|---|
| Microsoft | ML services for Windows and Office |
| Netflix | Dispatch crisis management framework |
| Uber | Real-time backend APIs |
| Cisco | API-first development |
| JPMorgan | Financial services APIs |
| Hugging Face | ML model serving infrastructure |
| Explosion (spaCy) | NLP model APIs |
| ING Bank | Banking APIs |

<!-- level:intermediate -->
## Real-World Adoption Patterns

### The ML/AI Pipeline

FastAPI has become the framework of choice in the ML/AI ecosystem. The reason is a natural fit between Pydantic models and the structured input/output of ML systems:

```python
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import asyncio

app = FastAPI()

class TrainingRequest(BaseModel):
    dataset_url: str
    model_type: str
    hyperparameters: dict

class TrainingStatus(BaseModel):
    job_id: str
    status: str
    progress: float | None = None

# In-memory job store (use Redis/database in production)
jobs: dict[str, TrainingStatus] = {}

async def train_model(job_id: str, request: TrainingRequest):
    jobs[job_id] = TrainingStatus(job_id=job_id, status="training", progress=0.0)
    # Simulate training
    for i in range(10):
        await asyncio.sleep(1)
        jobs[job_id].progress = (i + 1) / 10
    jobs[job_id].status = "completed"

@app.post("/train", response_model=TrainingStatus)
async def start_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
):
    import uuid
    job_id = str(uuid.uuid4())
    background_tasks.add_task(train_model, job_id, request)
    return TrainingStatus(job_id=job_id, status="queued")

@app.get("/train/{job_id}", response_model=TrainingStatus)
async def get_training_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]
```

Hugging Face's 2025 benchmarks showed FastAPI serving LLM responses at 200ms compared to Django's 650ms for the same workload.

### Netflix's Dispatch Framework

Netflix open-sourced Dispatch, a crisis management orchestration framework built entirely on FastAPI. Dispatch coordinates incident response across multiple services (PagerDuty, Slack, Jira, etc.) and needs to:

- Handle many concurrent webhook notifications
- Serve a real-time dashboard
- Process complex workflows asynchronously
- Integrate with dozens of external services

FastAPI's async support and dependency injection made it the natural choice.

### API Gateway Pattern

Organizations use FastAPI as a lightweight API gateway that aggregates multiple backend services:

```python
import httpx
from fastapi import FastAPI

app = FastAPI()

async_client = httpx.AsyncClient()

@app.get("/dashboard/{user_id}")
async def get_dashboard(user_id: int):
    # Fan out to multiple services concurrently
    user_task = async_client.get(f"http://user-service/users/{user_id}")
    orders_task = async_client.get(f"http://order-service/users/{user_id}/orders")
    notifications_task = async_client.get(
        f"http://notification-service/users/{user_id}/unread"
    )

    # Wait for all concurrently
    user_resp, orders_resp, notifications_resp = await asyncio.gather(
        user_task, orders_task, notifications_task
    )

    return {
        "user": user_resp.json(),
        "recent_orders": orders_resp.json(),
        "notifications": notifications_resp.json(),
    }
```

### Adoption by Numbers (2025-2026)

- **Developer adoption**: 38% of Python developers use FastAPI (JetBrains survey 2025)
- **PyPI downloads**: 4,000,000+ weekly
- **GitHub stars**: ~97,000 (surpassed Flask in late 2025)
- **Year-over-year growth**: 35-40% adoption increase
- **Stack Overflow**: Five-percentage-point surge in 2025 survey

### Industries Where FastAPI Thrives

1. **FinTech**: Low-latency APIs for trading, payment processing
2. **HealthTech**: HIPAA-compliant medical data APIs
3. **AI/ML**: Model serving, data pipelines, MLOps platforms
4. **IoT**: High-concurrency device communication
5. **SaaS**: Multi-tenant API backends
6. **E-commerce**: Catalog APIs, recommendation services

<!-- level:advanced -->
## Architectural Patterns at Scale

### Event-Driven Architecture with FastAPI

FastAPI integrates well with message brokers for event-driven architectures:

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
import aio_pika

connection = None
channel = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global connection, channel
    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
    channel = await connection.channel()
    # Declare exchange and queue
    exchange = await channel.declare_exchange("events", aio_pika.ExchangeType.TOPIC)
    queue = await channel.declare_queue("order_events")
    await queue.bind(exchange, routing_key="order.*")

    # Start consuming
    await queue.consume(process_event)
    yield

    await connection.close()

app = FastAPI(lifespan=lifespan)

async def process_event(message: aio_pika.IncomingMessage):
    async with message.process():
        event_data = json.loads(message.body)
        await handle_order_event(event_data)

@app.post("/orders/")
async def create_order(order: OrderCreate):
    saved_order = await save_order(order)
    # Publish event
    await channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps({"order_id": saved_order.id}).encode()),
        routing_key="order.created",
    )
    return saved_order
```

### CQRS Pattern (Command Query Responsibility Segregation)

```python
from fastapi import FastAPI, APIRouter

# Separate routers for commands and queries
command_router = APIRouter(prefix="/commands", tags=["commands"])
query_router = APIRouter(prefix="/queries", tags=["queries"])

# Commands mutate state (write to primary DB)
@command_router.post("/orders/")
async def create_order(order: OrderCreate, db: WriterDb):
    new_order = await db.execute(insert(Order).values(**order.model_dump()))
    # Publish event for read-model update
    await publish_event("order.created", new_order)
    return {"id": new_order.id}

# Queries read from optimized read models (could be different DB)
@query_router.get("/orders/")
async def list_orders(db: ReaderDb, filters: OrderFilters = Depends()):
    # Read from denormalized, query-optimized store
    return await db.execute(
        select(OrderReadModel)
        .where(OrderReadModel.status == filters.status)
        .order_by(OrderReadModel.created_at.desc())
    )

app = FastAPI()
app.include_router(command_router)
app.include_router(query_router)
```

### FastAPI as BFF (Backend For Frontend)

The Backend For Frontend pattern uses a dedicated API layer tailored to each frontend's needs:

```python
# Mobile BFF -- minimal data, optimized for bandwidth
mobile_app = FastAPI(title="Mobile BFF")

@mobile_app.get("/feed")
async def mobile_feed(user: CurrentUser):
    """Returns minimal feed data optimized for mobile."""
    items = await get_feed_items(user.id, limit=20)
    return [
        {"id": i.id, "title": i.title, "thumb": i.thumbnail_url}
        for i in items
    ]

# Web BFF -- richer data for desktop experience
web_app = FastAPI(title="Web BFF")

@web_app.get("/feed")
async def web_feed(user: CurrentUser):
    """Returns rich feed data for web clients."""
    items = await get_feed_items(user.id, limit=50)
    return [
        {
            "id": i.id,
            "title": i.title,
            "description": i.description,
            "image": i.full_image_url,
            "author": i.author_name,
            "comments_count": i.comments_count,
            "related": i.related_ids[:3],
        }
        for i in items
    ]

# Mount both under a main app
main_app = FastAPI()
main_app.mount("/mobile", mobile_app)
main_app.mount("/web", web_app)
```

### Scaling Considerations

**Horizontal scaling (preferred)**:
- Run multiple instances behind a load balancer
- Use single-worker containers in Kubernetes
- Store session state in Redis/database, not in memory
- Use distributed task queues (Celery, Dramatiq) for heavy work

**Vertical scaling**:
- Increase Uvicorn workers (`--workers N`) to use all CPU cores
- Use Gunicorn as process manager for worker lifecycle
- Tune connection pool sizes for databases and HTTP clients
- Monitor event loop latency to detect blocking code

**Common production mistakes**:
- Running CPU-intensive code in async handlers (blocks event loop)
- Not setting connection pool limits (exhausting DB connections)
- Using in-memory state that is not shared across workers
- Forgetting to handle graceful shutdown (in-flight requests lost)
