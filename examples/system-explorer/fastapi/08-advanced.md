# Advanced Topics

<!-- level:beginner -->
## Beyond Basic APIs

Once you are comfortable with routes, models, and basic dependencies, FastAPI offers several advanced features for building sophisticated applications.

### Background Tasks

Sometimes you want to respond to the client immediately but do some work afterward (sending an email, processing data, writing a log):

```python
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

def send_notification(email: str, message: str):
    # This runs after the response is sent
    send_email(email, message)

@app.post("/signup/")
def signup(email: str, background_tasks: BackgroundTasks):
    create_user(email)
    background_tasks.add_task(send_notification, email, "Welcome!")
    return {"message": "User created"}  # Client gets this immediately
```

The client receives the response right away. The email is sent in the background.

### WebSockets

For real-time, bidirectional communication (chat, live updates, notifications):

```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"You said: {data}")
```

### Streaming Responses

For large files or real-time data feeds:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def generate_large_report():
    for i in range(1000):
        yield f"Row {i}: data...\n"

@app.get("/report")
async def get_report():
    return StreamingResponse(
        generate_large_report(),
        media_type="text/plain",
    )
```

### Static Files

Serve HTML, CSS, JS, and images alongside your API:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
# Files in ./static/ are now available at /static/...
```

<!-- level:intermediate -->
## Intermediate Advanced Patterns

### Server-Sent Events (SSE)

SSE is simpler than WebSockets for server-to-client push (e.g., live log streaming, progress updates):

```python
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def event_generator():
    """Generate SSE-formatted events."""
    counter = 0
    while True:
        counter += 1
        yield f"data: {{'count': {counter}, 'time': '{datetime.now().isoformat()}'}}\n\n"
        await asyncio.sleep(1)

@app.get("/events")
async def stream_events():
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
```

Client-side JavaScript:
```javascript
const eventSource = new EventSource("/events");
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Count:", data.count);
};
```

### WebSocket Chat Room

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/chat/{username}")
async def chat(websocket: WebSocket, username: str):
    await manager.connect(websocket)
    await manager.broadcast(f"{username} joined the chat")
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{username}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"{username} left the chat")
```

### Lifespan Events (Modern Approach)

The `lifespan` context manager replaces the older `on_event("startup")` / `on_event("shutdown")` pattern:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize shared resources
    app.state.http_client = httpx.AsyncClient()
    app.state.db_pool = await create_db_pool()

    print("Application started")
    yield  # Application runs here

    # Shutdown: clean up resources
    await app.state.http_client.aclose()
    await app.state.db_pool.close()
    print("Application shut down")

app = FastAPI(lifespan=lifespan)

@app.get("/external-data")
async def get_external(request: Request):
    client = request.app.state.http_client
    response = await client.get("https://api.example.com/data")
    return response.json()
```

### Custom Exception Handlers

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

app = FastAPI()

class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "path": str(request.url),
            }
        },
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        },
    )
```

### Advanced Dependency Injection

**Class-based dependencies**:
```python
class ItemFilter:
    def __init__(
        self,
        q: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        category: str | None = None,
    ):
        self.q = q
        self.min_price = min_price
        self.max_price = max_price
        self.category = category

    def apply(self, query):
        if self.q:
            query = query.where(Item.name.ilike(f"%{self.q}%"))
        if self.min_price is not None:
            query = query.where(Item.price >= self.min_price)
        if self.max_price is not None:
            query = query.where(Item.price <= self.max_price)
        if self.category:
            query = query.where(Item.category == self.category)
        return query

@app.get("/items/")
async def list_items(
    filters: ItemFilter = Depends(),
    db: DbSession = Depends(),
):
    query = filters.apply(select(Item))
    return (await db.scalars(query)).all()
```

**Parameterized dependencies**:
```python
def require_role(role: str):
    async def check_role(current_user: CurrentUser):
        if role not in current_user.roles:
            raise HTTPException(status_code=403, detail=f"Role '{role}' required")
        return current_user
    return check_role

@app.delete("/admin/users/{user_id}", dependencies=[Depends(require_role("admin"))])
async def delete_user(user_id: int):
    ...

@app.get("/editor/posts/", dependencies=[Depends(require_role("editor"))])
async def manage_posts():
    ...
```

<!-- level:advanced -->
## Expert-Level Patterns

### Custom APIRoute for Request/Response Transformation

Override how FastAPI processes requests at the route level:

```python
from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute
import gzip
import time

class TimedRoute(APIRoute):
    def get_route_handler(self):
        original_handler = super().get_route_handler()

        async def timed_handler(request: Request) -> Response:
            start = time.perf_counter()
            response = await original_handler(request)
            duration = time.perf_counter() - start
            response.headers["X-Response-Time"] = f"{duration:.4f}"
            return response

        return timed_handler

class GzipRoute(APIRoute):
    def get_route_handler(self):
        original_handler = super().get_route_handler()

        async def gzip_handler(request: Request) -> Response:
            # Decompress gzipped request bodies
            if request.headers.get("content-encoding") == "gzip":
                body = await request.body()
                request._body = gzip.decompress(body)
            return await original_handler(request)

        return gzip_handler

# Apply to specific routers
router = APIRouter(route_class=TimedRoute)
```

### WebSocket with Authentication and Heartbeat

```python
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query

app = FastAPI()

async def ws_auth(websocket: WebSocket, token: str = Query(...)):
    """Authenticate WebSocket connections via query parameter."""
    user = verify_token(token)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return None
    return user

@app.websocket("/ws/feed")
async def live_feed(websocket: WebSocket):
    token = websocket.query_params.get("token")
    user = verify_token(token)
    if not user:
        await websocket.close(code=4001)
        return

    await websocket.accept()

    # Background heartbeat to detect dead connections
    async def heartbeat():
        while True:
            try:
                await asyncio.sleep(30)
                await websocket.send_json({"type": "ping"})
            except Exception:
                break

    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        while True:
            message = await websocket.receive_json()
            if message.get("type") == "subscribe":
                channel = message["channel"]
                # Subscribe to a Redis pub/sub channel
                await subscribe_user(user.id, channel, websocket)
            elif message.get("type") == "pong":
                pass  # Heartbeat acknowledged
    except WebSocketDisconnect:
        heartbeat_task.cancel()
        await unsubscribe_user(user.id)
```

### Streaming LLM Responses (AI/ML Pattern)

A very common pattern in 2025-2026 AI applications:

```python
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    stream: bool = True

async def stream_llm_response(messages: list[ChatMessage]):
    """Stream tokens from an LLM."""
    # Example: calling an async LLM client
    async for chunk in llm_client.chat_stream(
        messages=[{"role": m.role, "content": m.content} for m in messages]
    ):
        # SSE format
        yield f"data: {json.dumps({'token': chunk.text})}\n\n"
    yield "data: [DONE]\n\n"

@app.post("/chat")
async def chat(request: ChatRequest):
    if request.stream:
        return StreamingResponse(
            stream_llm_response(request.messages),
            media_type="text/event-stream",
        )
    else:
        response = await llm_client.chat(
            messages=[{"role": m.role, "content": m.content} for m in request.messages]
        )
        return {"response": response.text}
```

### Testing Async Applications Thoroughly

```python
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

@pytest.mark.anyio
async def test_concurrent_requests(client: AsyncClient):
    """Test that the server handles concurrent requests correctly."""
    tasks = [
        client.get(f"/items/{i}")
        for i in range(100)
    ]
    responses = await asyncio.gather(*tasks)
    assert all(r.status_code == 200 for r in responses)

@pytest.mark.anyio
async def test_websocket():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        async with client.stream("GET", "/ws") as ws:
            # WebSocket testing requires httpx-ws or similar
            pass

@pytest.mark.anyio
async def test_with_mocked_dependency(client: AsyncClient):
    """Test with a mocked external service."""
    mock_response = {"id": 1, "name": "Test Item"}

    async def mock_get_item(item_id: int):
        return mock_response

    app.dependency_overrides[get_item_service] = lambda: mock_get_item
    response = await client.get("/items/1")
    assert response.json() == mock_response
    app.dependency_overrides.clear()
```

### Middleware vs Dependencies: When to Use Which

```
Middleware:
  - Runs for EVERY request (including 404s, static files)
  - Cannot access path operation parameters
  - Good for: logging, timing, CORS, compression, security headers

Dependencies:
  - Runs only for matched routes
  - Has access to path/query/body parameters
  - Can be cached per request
  - Can use yield for cleanup
  - Good for: auth, DB sessions, rate limiting, input transformation

Rule of thumb:
  - Cross-cutting concerns that don't need route context -> Middleware
  - Route-specific logic or resource management -> Dependencies
```

### Mounting Sub-Applications for Isolation

```python
# Each sub-app has its own exception handlers, middleware, and OpenAPI schema
from fastapi import FastAPI

# Public API
public_api = FastAPI(title="Public API")

@public_api.get("/products/")
async def list_products():
    return [...]

# Internal API (different auth, different docs)
internal_api = FastAPI(title="Internal API", docs_url=None)

@internal_api.get("/metrics/")
async def get_metrics():
    return [...]

# Main application
app = FastAPI()
app.mount("/public", public_api)
app.mount("/internal", internal_api)
```
