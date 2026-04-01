# Tradeoffs & Alternatives

<!-- level:beginner -->
## When to Use FastAPI (and When Not To)

No framework is perfect for every situation. Understanding where FastAPI excels and where it falls short helps you make the right choice.

### FastAPI Strengths

- **API-first development**: Purpose-built for building REST APIs and microservices
- **Developer experience**: Type hints, autocomplete, automatic docs
- **Performance**: One of the fastest Python frameworks
- **Modern Python**: Built on async/await, type hints, Pydantic
- **Low learning curve**: If you know Python type hints, you know most of FastAPI
- **Great documentation**: The official docs are widely praised as excellent

### FastAPI Limitations

- **Not a full-stack framework**: No built-in ORM, admin panel, or templating (unlike Django)
- **Young ecosystem**: Fewer third-party packages than Django or Flask
- **Async complexity**: Async programming introduces new categories of bugs
- **No built-in database migrations**: You need Alembic or similar
- **Still 0.x version**: Technically pre-1.0 (though stable in practice)

### Quick Decision Guide

| Need | Best Choice |
|---|---|
| JSON REST API | **FastAPI** |
| Full-stack web app with admin | **Django** |
| Quick prototype / minimal API | **Flask** or **FastAPI** |
| Maximum raw performance in Python | **Litestar** or **Starlette** |
| Existing Flask/Django codebase | Keep what you have |
| ML model serving | **FastAPI** |
| Real-time WebSocket app | **FastAPI** or **Starlette** |
| Content management / CMS | **Django** |
| Enterprise with large team | **Django** (more structure) |
| Microservices | **FastAPI** |

### The Main Alternatives

**Django** -- The "batteries included" framework (2005). Comes with ORM, admin panel, auth, templates, migrations, and more. Best for full-stack web applications.

**Flask** -- The original Python micro-framework (2010). Minimal core, extend with plugins. Best for simplicity and flexibility.

**Litestar** -- A newer ASGI framework (formerly Starlite). Focuses on performance and clean API design. Competes directly with FastAPI.

**Starlette** -- The ASGI toolkit that FastAPI builds on. Use directly if you want maximum performance without FastAPI's overhead.

<!-- level:intermediate -->
## Detailed Framework Comparison

### FastAPI vs Django

```
Feature               | FastAPI              | Django
-------------------  |---------------------|-----------------------
Architecture          | Micro + ASGI         | Full-stack + WSGI/ASGI
ORM                   | None (bring your own)| Built-in (Django ORM)
Admin panel           | None                 | Built-in (excellent)
Auth system           | DIY + OAuth2 utils   | Built-in (complete)
API docs              | Auto-generated       | Via django-rest-framework
Async support         | Native (first-class) | Added (Django 4.1+)
Template engine       | Optional (Jinja2)    | Built-in (Django templates)
Database migrations   | Alembic (external)   | Built-in (manage.py migrate)
Performance           | ~15-20k req/s        | ~2-3k req/s (DRF)
Learning curve        | Low-medium           | Medium-high
Community size        | Growing fast         | Very large, mature
Job market            | Growing              | Large, established
```

**Choose Django when**: You need a complete web application (not just an API), want an admin panel, need a mature ORM with migrations, or your team is already familiar with Django.

**Choose FastAPI when**: You are building an API-only backend, need high performance, want modern Python features, or are building microservices.

Django REST Framework (DRF) is Django's answer to API development. It is mature and powerful, but heavier and slower than FastAPI. If you already have a Django application and want to add an API, DRF is the natural choice. For greenfield API projects, FastAPI is usually the better starting point.

### FastAPI vs Flask

```
Feature               | FastAPI              | Flask
-------------------  |---------------------|-----------------------
Type hints            | Core feature         | Not used by framework
Validation            | Automatic (Pydantic) | Manual or Flask-Pydantic
API docs              | Auto-generated       | Via flask-smorest/apispec
Async support         | Native               | Limited (Flask 2.0+)
Performance           | ~15-20k req/s        | ~2-4k req/s
Dependency injection  | Built-in             | None (use Flask-Injector)
WebSocket support     | Built-in             | Via Flask-SocketIO
Server                | ASGI (Uvicorn)       | WSGI (Gunicorn)
```

```python
# Flask approach
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/items/<int:item_id>")
def get_item(item_id):
    q = request.args.get("q")  # Manual extraction
    # No automatic validation
    return jsonify({"item_id": item_id, "q": q})

# FastAPI approach
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
def get_item(item_id: int, q: str | None = None):
    # Automatic validation, documentation, and type conversion
    return {"item_id": item_id, "q": q}
```

**Choose Flask when**: You want maximum simplicity, have an existing Flask codebase, need extensive third-party plugin support (Flask has a huge ecosystem), or prefer a framework that stays out of your way.

**Choose FastAPI when**: You want automatic validation and documentation, need async support, want better performance, or prefer type-hint-driven development.

### FastAPI vs Litestar

Litestar (formerly Starlite) is FastAPI's most direct competitor:

```
Feature               | FastAPI              | Litestar
-------------------  |---------------------|-----------------------
Validation library    | Pydantic             | msgspec or Pydantic
Performance           | ~15-20k req/s        | ~20-25k req/s
Dependency injection  | Built-in (simple)    | Built-in (more formal)
OpenAPI generation    | Built-in             | Built-in
Community size        | Very large (~97k *)  | Small (~6k *)
Documentation         | Excellent            | Good
Maturity              | 7+ years             | ~3 years
DTO layer             | response_model       | Built-in DTO system
Middleware            | Starlette-based      | Custom implementation
WebSockets            | Supported            | Supported
Testing               | httpx/TestClient     | Built-in test client
```

**Choose Litestar when**: You need the absolute highest performance in Python, want a more opinionated/structured framework, prefer msgspec over Pydantic, or want built-in DTO support.

**Choose FastAPI when**: You want a larger community and ecosystem, prefer Pydantic, value extensive documentation and tutorials, or need maximum third-party library support.

### FastAPI vs Starlette (Direct)

Since FastAPI builds on Starlette, using Starlette directly gives you slightly better performance at the cost of implementing validation, serialization, and documentation yourself:

```python
# Starlette -- manual everything
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

async def get_item(request):
    item_id = request.path_params["item_id"]
    # Manual validation
    try:
        item_id = int(item_id)
    except ValueError:
        return JSONResponse({"error": "Invalid ID"}, status_code=400)
    return JSONResponse({"item_id": item_id})

app = Starlette(routes=[Route("/items/{item_id}", get_item)])

# FastAPI -- automatic everything
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
def get_item(item_id: int):  # Validation is automatic
    return {"item_id": item_id}
```

Use raw Starlette only if you have measured that FastAPI's overhead matters for your use case (rare) or if you are building a framework on top of Starlette yourself.

<!-- level:advanced -->
## Nuanced Tradeoffs for Experienced Developers

### The Async Tax

FastAPI's biggest hidden cost is the complexity of async programming:

**Footguns**:
1. **Accidentally blocking the event loop**: A single `time.sleep(5)` in an `async def` handler blocks ALL concurrent requests for 5 seconds.
2. **Mixing sync and async ORMs**: Using synchronous SQLAlchemy in an `async def` handler without `run_in_executor` will block.
3. **Testing complexity**: Async tests require `pytest-anyio` or `pytest-asyncio`, special fixtures, and careful event loop management.
4. **Debugging difficulty**: Async tracebacks are harder to read. `await` chains obscure the call stack.
5. **Library compatibility**: Not all Python libraries support async. You may need sync wrappers.

**Mitigation**: FastAPI transparently handles sync functions in thread pools. If your entire stack is synchronous (sync DB driver, sync HTTP client), use regular `def` handlers and let FastAPI thread-pool them. You still get the benefits of validation, docs, and DI without the async complexity.

### Type Hint Coupling

FastAPI's reliance on type hints is both its greatest strength and a coupling risk:

- Your API contract is defined in Python code, not in a separate schema file
- Changing a Pydantic model changes both validation AND the OpenAPI schema
- There is no easy way to have different validation rules and documentation
- Pydantic V1 to V2 migration was painful for many projects

**Schema-first alternative**: If you want the schema to be the source of truth (not the Python code), consider generating FastAPI code from an OpenAPI spec using tools like `openapi-python-client` or `datamodel-code-generator`.

### Dependency Injection Limitations

FastAPI's DI is simple and effective, but has limitations compared to formal DI containers:

1. **No scopes beyond request**: There is no built-in "session scope", "application scope", etc. You implement these with lifespan events and `app.state`.
2. **No lazy injection**: Dependencies are resolved eagerly for every request, even if the handler does not use them in a particular code path.
3. **Global overrides only**: `app.dependency_overrides` is global. If two test files override the same dependency differently and run in parallel, they interfere.
4. **No circular dependency detection**: The framework does not detect circular dependency graphs at startup. They will cause infinite recursion at runtime.

### Comparison of Validation Approaches

```python
# FastAPI/Pydantic: Declarative, type-hint-based
class CreateUser(BaseModel):
    email: EmailStr
    age: int = Field(ge=18, le=120)
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")

# Django REST Framework: Serializer-based
class CreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    age = serializers.IntegerField(min_value=18, max_value=120)
    username = serializers.RegexField(r"^[a-zA-Z0-9_]+$", min_length=3, max_length=50)

# Flask + Marshmallow: Schema-based
class CreateUserSchema(Schema):
    email = fields.Email(required=True)
    age = fields.Integer(required=True, validate=Range(min=18, max=120))
    username = fields.String(required=True, validate=Length(min=3, max=50))

# Litestar + msgspec: Struct-based (fastest)
class CreateUser(msgspec.Struct):
    email: str
    age: Annotated[int, msgspec.Meta(ge=18, le=120)]
    username: Annotated[str, msgspec.Meta(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")]
```

### The "Good Enough" Factor

In practice, the performance differences between Python web frameworks rarely matter because:

1. **Database queries dominate**: A 50ms database query dwarfs a 0.1ms framework overhead difference
2. **Network latency dominates**: A 100ms network round-trip makes framework speed irrelevant
3. **Python itself is the bottleneck**: If you need truly high throughput, you need Go/Rust/Java, not a different Python framework

The real reasons to choose FastAPI over alternatives are:
- Developer productivity (type hints, autocomplete, auto-docs)
- Code correctness (automatic validation catches bugs early)
- Ecosystem fit (ML/AI ecosystem uses FastAPI heavily)
- Team preferences (most Python developers now prefer FastAPI for new API projects)

### Migration Considerations

**Flask to FastAPI** (most common migration path):

```python
# Flask
@app.route("/users", methods=["GET"])
def list_users():
    page = request.args.get("page", 1, type=int)
    users = User.query.paginate(page=page)
    return jsonify([u.to_dict() for u in users.items])

# FastAPI equivalent
@app.get("/users", response_model=list[UserResponse])
def list_users(page: int = Query(1, ge=1)):
    return get_paginated_users(page)
```

Key migration steps:
1. Replace `@app.route` with HTTP-method-specific decorators
2. Move request parsing to function parameters with type hints
3. Replace `request.args.get()` / `request.json` with Pydantic models
4. Replace `jsonify()` with direct dict/model returns
5. Add `response_model` for automatic response filtering
6. Convert Flask extensions to FastAPI equivalents (or use raw libraries)

The migration can be gradual: mount a FastAPI app inside Flask (or vice versa) using ASGI/WSGI adapters.

### Final Assessment

FastAPI represents the current state of the art for Python API development. It successfully synthesizes ideas from a decade of framework evolution (Django, Flask, APIStar, NestJS) into a cohesive, type-safe, high-performance package. Its main risk is coupling to Pydantic (a single library's design decisions become your API's contract), but the benefits of developer productivity and correctness far outweigh this for the vast majority of projects.

For new Python API projects in 2026, FastAPI is the default recommendation unless you have a specific reason to choose otherwise (full-stack needs -> Django, maximum raw performance -> Litestar, existing codebase -> keep it).
