# Core Concepts

<!-- level:beginner -->
## The Big Ideas

FastAPI is built around a few core ideas that, once understood, make the entire framework feel intuitive.

### 1. Type Hints Drive Everything

In FastAPI, Python type hints are not just for documentation or editor support -- they are functional. The framework reads your type annotations at runtime and uses them to:

- Validate incoming data (reject bad requests with clear error messages)
- Convert data types (turn a URL path string into a Python `int`)
- Generate API documentation (produce an OpenAPI schema automatically)
- Power editor autocomplete (your IDE knows the shape of every parameter)

```python
from fastapi import FastAPI

app = FastAPI()

# The type hint `item_id: int` does three things:
# 1. Validates that item_id is an integer
# 2. Converts the URL string to a Python int
# 3. Documents the parameter in the OpenAPI schema
@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}
```

If a client sends `GET /items/abc`, FastAPI automatically returns a 422 Unprocessable Entity response with a clear error message -- you never write validation code.

### 2. Pydantic Models for Request/Response Bodies

For complex data (JSON bodies, nested objects), you define Pydantic models:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    description: str | None = None
    tax: float | None = None

@app.post("/items/")
def create_item(item: Item):
    total = item.price + (item.tax or 0)
    return {"name": item.name, "total_price": total}
```

When a client sends a POST request:
- The JSON body is parsed into an `Item` instance
- All fields are validated (name must be a string, price must be a float)
- Optional fields default to `None` if not provided
- If validation fails, a detailed 422 error is returned automatically

### 3. Path Operations (Routes)

FastAPI uses decorator-based routing, similar to Flask. Each HTTP method has its own decorator:

```python
@app.get("/items/")       # Handle GET requests
@app.post("/items/")      # Handle POST requests
@app.put("/items/{id}")   # Handle PUT requests
@app.delete("/items/{id}")# Handle DELETE requests
@app.patch("/items/{id}") # Handle PATCH requests
```

### 4. Automatic Documentation

Every FastAPI application gets two documentation UIs for free:

- **Swagger UI** at `/docs` -- Interactive, lets you try out API calls
- **ReDoc** at `/redoc` -- Clean, readable reference documentation

Both are generated automatically from your code's type hints and Pydantic models. You never write OpenAPI YAML by hand.

### 5. Dependency Injection

Instead of importing shared logic or using global state, you declare what your endpoint needs:

```python
from fastapi import FastAPI, Depends

app = FastAPI()

def get_db():
    db = DatabaseSession()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/")
def get_users(db = Depends(get_db)):
    return db.query(User).all()
```

FastAPI calls `get_db()` for you, passes the result to your function, and handles cleanup after the response is sent.

<!-- level:intermediate -->
## Deeper Concept Exploration

### Parameter Sources

FastAPI can extract parameters from multiple parts of an HTTP request, all using the same type-hint pattern:

```python
from fastapi import FastAPI, Query, Path, Header, Cookie, Body

app = FastAPI()

@app.get("/items/{item_id}")
def read_item(
    item_id: int = Path(..., ge=1, description="The ID of the item"),
    q: str | None = Query(None, max_length=50),
    user_agent: str | None = Header(None),
    session_id: str | None = Cookie(None),
):
    return {
        "item_id": item_id,
        "query": q,
        "user_agent": user_agent,
        "session_id": session_id,
    }
```

The pattern is consistent: the parameter's source is determined by its default value (`Path`, `Query`, `Header`, `Cookie`, `Body`). FastAPI uses this to know where to look for the data.

### Response Models

You can declare what your endpoint returns, and FastAPI will filter the response accordingly:

```python
from pydantic import BaseModel

class UserIn(BaseModel):
    username: str
    password: str
    email: str

class UserOut(BaseModel):
    username: str
    email: str

@app.post("/users/", response_model=UserOut)
def create_user(user: UserIn):
    # Even though we have the password internally,
    # the response will only include username and email
    save_user(user)
    return user  # FastAPI filters out `password` automatically
```

This is a powerful security pattern: you can work with full internal models but expose only safe fields.

### Status Codes and Response Types

```python
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

app = FastAPI()

@app.post("/items/", status_code=status.HTTP_201_CREATED)
def create_item(item: Item):
    return item

@app.get("/page", response_class=HTMLResponse)
def get_page():
    return "<html><body><h1>Hello</h1></body></html>"

@app.get("/old-path")
def redirect():
    return RedirectResponse(url="/new-path")
```

### Error Handling

FastAPI provides structured error handling via `HTTPException`:

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

items = {"foo": "The Foo Item"}

@app.get("/items/{item_id}")
def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "Item lookup failed"},
        )
    return {"item": items[item_id]}
```

You can also register custom exception handlers:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

class ItemNotFoundException(Exception):
    def __init__(self, item_id: str):
        self.item_id = item_id

@app.exception_handler(ItemNotFoundException)
async def item_not_found_handler(request: Request, exc: ItemNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"message": f"Item {exc.item_id} does not exist"},
    )
```

### Async and Sync: The Dual Nature

FastAPI handles both async and sync functions transparently:

```python
# Async handler -- runs directly on the event loop
@app.get("/async-items/")
async def read_items_async():
    items = await fetch_items_from_db()
    return items

# Sync handler -- FastAPI runs this in a thread pool automatically
@app.get("/sync-items/")
def read_items_sync():
    items = fetch_items_from_db_sync()
    return items
```

**Rule of thumb**: Use `async def` when calling `await`-able code (async DB drivers, HTTP clients). Use plain `def` for blocking I/O (synchronous DB drivers, file system operations). FastAPI handles the threading for you.

<!-- level:advanced -->
## Concepts Under the Hood

### How Type Hints Become Validation

When FastAPI processes a path operation function, it performs several steps at startup time:

1. **Signature inspection**: Uses `inspect.signature()` to read all parameters and their type annotations.
2. **Dependency resolution**: Identifies parameters with `Depends()` defaults and builds a dependency graph.
3. **Parameter classification**: Determines the source of each parameter (path, query, body, header, cookie) based on the annotation and default value.
4. **Pydantic model generation**: For each parameter, FastAPI creates or references a Pydantic model/field that encodes the validation rules.
5. **OpenAPI schema emission**: The Pydantic models are converted to JSON Schema, which is embedded in the OpenAPI specification.

This happens once at application startup, not per-request. The result is a compiled dependency-resolution function that runs efficiently for each request.

### The Annotated Pattern (Modern FastAPI)

Modern FastAPI (0.95+) encourages `Annotated` for dependency and parameter declarations:

```python
from typing import Annotated
from fastapi import Depends, Query

# Instead of:
# def read_items(q: str = Query(max_length=50)):

# Use:
def read_items(q: Annotated[str, Query(max_length=50)]):
    return {"q": q}
```

The `Annotated` approach has several advantages:
- The type hint and the FastAPI metadata are separated clearly
- The same annotated type can be reused across multiple endpoints
- It works better with tools like `mypy` because the base type is preserved
- Dependencies can be stored as reusable type aliases

```python
# Reusable dependency type
CurrentUser = Annotated[User, Depends(get_current_user)]

@app.get("/me")
def get_me(user: CurrentUser):
    return user

@app.get("/my-items")
def get_my_items(user: CurrentUser):
    return get_items_for_user(user)
```

### Request Lifecycle in Detail

```
Client Request
    |
    v
ASGI Server (Uvicorn)
    |
    v
Starlette Middleware Stack (outermost first)
    |
    v
FastAPI Router (matches path operation)
    |
    v
Dependency Resolution (depth-first, cached per request)
    |
    v
Request Validation (Pydantic parses/validates all inputs)
    |
    v
Path Operation Function (your code runs here)
    |
    v
Response Serialization (Pydantic serializes, response_model filters)
    |
    v
Middleware Stack (reverse order, response phase)
    |
    v
ASGI Server sends response
    |
    v
Background Tasks run (if any)
    |
    v
Dependency cleanup (yield-based dependencies finalize)
```

### Pydantic V2 Integration

Since FastAPI 0.100+, Pydantic V2 (written in Rust via pydantic-core) is fully supported. This brings:

- **5-50x faster validation** compared to Pydantic V1
- **Strict mode** that disables type coercion when desired
- **Computed fields** for derived values in response models
- **Custom serializers** for fine-grained output control

```python
from pydantic import BaseModel, field_validator, computed_field

class Product(BaseModel):
    name: str
    price: float
    quantity: int

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be positive")
        return round(v, 2)

    @computed_field
    @property
    def total_value(self) -> float:
        return round(self.price * self.quantity, 2)
```

### OpenAPI 3.1 and JSON Schema

FastAPI generates OpenAPI 3.1 schemas, which use standard JSON Schema (2020-12). This means:
- Nullable fields use `{"anyOf": [{"type": "string"}, {"type": "null"}]}` instead of the old `nullable: true`
- `const` replaces `enum` for single-value constraints
- `$ref` can have sibling keywords
- `examples` (plural) is supported alongside `example`

This matters because the OpenAPI schema is the contract that client generators, documentation tools, and testing frameworks consume.
