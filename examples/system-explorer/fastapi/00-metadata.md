# Metadata & Overview

<!-- level:beginner -->
## What Is FastAPI?

FastAPI is a modern, high-performance Python web framework for building APIs. Created by Sebastian Ramirez (tiangolo) and first released in December 2018, it has rapidly become one of the most popular Python web frameworks in existence.

At its core, FastAPI lets you write web APIs using standard Python type hints. This single design decision unlocks automatic request validation, serialization, and interactive documentation -- all with minimal boilerplate code.

### The Elevator Pitch

If you know Python and type hints, you already know most of FastAPI. Here is a complete, working API:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
```

That is a fully functional API with:
- Automatic input validation (`item_id` must be an integer)
- Optional query parameters (`q` defaults to `None`)
- Auto-generated interactive documentation at `/docs` and `/redoc`
- JSON serialization of the response

### Key Claims (from official docs)

- **Performance**: On par with Node.js and Go, thanks to Starlette and Pydantic
- **Developer speed**: Increases feature development speed by 200-300%
- **Fewer bugs**: Reduces human-induced errors by approximately 40%
- **Intuitive**: Full editor support with autocomplete everywhere
- **Standards-based**: Built on OpenAPI (formerly Swagger) and JSON Schema

### Project Vitals

| Metric | Value |
|---|---|
| First release | December 2018 |
| GitHub stars | ~97,000 (as of early 2026) |
| GitHub forks | ~9,000+ |
| PyPI weekly downloads | 4,000,000+ |
| License | MIT |
| Python versions | 3.8+ |
| Creator | Sebastian Ramirez (@tiangolo) |
| GitHub organization | github.com/fastapi |

### Who Uses FastAPI?

Major organizations using FastAPI in production include:

- **Microsoft** -- ML services, integrated into Windows and Office products
- **Netflix** -- Dispatch crisis management framework
- **Uber** -- Backend APIs for real-time, high-concurrency data processing
- **Cisco** -- API-first development strategy
- **JPMorgan** -- Financial services APIs
- **Hugging Face** -- ML model serving infrastructure

<!-- level:intermediate -->
## Framework Positioning and Philosophy

FastAPI occupies a specific niche in the Python web framework landscape. It is not a full-stack framework like Django; it is not a minimalist micro-framework like Flask. It is purpose-built for API development, combining ideas from both traditions.

### Design Philosophy

FastAPI is built on several core principles:

1. **Type hints are the single source of truth.** Parameter types, request bodies, query parameters, and response models are all defined via Python type annotations. The framework extracts validation rules, serialization logic, and documentation from these annotations.

2. **Standards over proprietary abstractions.** FastAPI generates an OpenAPI 3.1 schema for every application. This means your API documentation, client generation, and testing tools all work out of the box.

3. **Developer experience is a feature.** Editor support (autocomplete, inline errors, type checking) is treated as first-class. The framework is designed so that `mypy` and editors like VS Code or PyCharm can understand your entire API surface.

4. **Async-first, sync-compatible.** FastAPI uses ASGI natively but transparently runs synchronous handler functions in a thread pool, so you never have to choose up front.

### Adoption Trajectory

FastAPI's adoption has been remarkably fast:

- 2020: ~15,000 GitHub stars
- 2023: ~60,000 GitHub stars
- 2025: ~88,000 GitHub stars (surpassing Flask)
- 2026: ~97,000 GitHub stars

The 2025 JetBrains Python Developer Survey showed FastAPI usage jumping from 29% to 38% among Python developers -- a 40% year-over-year increase.

### The Two Pillars

FastAPI does not exist in isolation. It is built on top of two foundational libraries:

```
+-------------------+
|     FastAPI        |  <-- Your API logic, DI, security, docs
+-------------------+
|    Starlette       |  <-- ASGI toolkit: routing, middleware, WebSockets
+-------------------+
|    Pydantic        |  <-- Data validation, serialization, settings
+-------------------+
|  Uvicorn / Hypercorn  |  <-- ASGI server
+-------------------+
```

- **Starlette** provides the web layer: routing, middleware, WebSocket support, background tasks, startup/shutdown events, and test client.
- **Pydantic** provides data validation: model definitions, JSON Schema generation, serialization/deserialization, and settings management.

FastAPI is, in essence, a carefully designed layer that wires Starlette routing to Pydantic models using Python type hints, and adds dependency injection, security utilities, and OpenAPI generation on top.

<!-- level:advanced -->
## Technical Identity and Lineage

### Inspiration Chain

FastAPI's design was directly informed by a specific sequence of projects:

1. **Django REST Framework** -- Proved that auto-generated API documentation was valuable
2. **Flask** -- Showed that a micro-framework with decorators could be the ideal developer interface
3. **APIStar (<=0.5)** -- Tom Christie's framework that first combined type hints with OpenAPI generation (the spiritual predecessor to FastAPI)
4. **Requests** -- Inspired the "simple API with sensible defaults" philosophy
5. **Marshmallow / Webargs** -- Showed the value of declarative validation, but predated type hints
6. **NestJS** -- Demonstrated that dependency injection and type declarations could unify validation and documentation
7. **Molten** -- First Python framework to use type hints for DI and validation, but lacked ASGI

When Tom Christie (APIStar's creator) pivoted to building Starlette as a pure ASGI toolkit, Sebastian Ramirez recognized the opportunity: combine Starlette's performance foundation with Pydantic's type-hint-based validation to create the framework APIStar was trying to be.

### Class Hierarchy

FastAPI's `FastAPI` class inherits directly from `Starlette`:

```python
# Simplified from fastapi/applications.py
class FastAPI(Starlette):
    def __init__(self, ...):
        # Sets up OpenAPI schema generation
        # Configures dependency injection
        # Adds API router
        ...
```

This means every Starlette feature is available in FastAPI. You can use Starlette middleware, mount ASGI sub-applications, and access the raw ASGI interface when needed.

### Version History Highlights

- **0.1.0 (Dec 2018)**: Initial release with core routing, Pydantic integration, OpenAPI
- **0.65.0 (2021)**: `Annotated` support for dependencies
- **0.95.0 (2023)**: Pydantic v2 support (major performance improvement)
- **0.100.0 (2023)**: Lifespan context managers replace startup/shutdown events
- **0.109.0+ (2024)**: OpenAPI 3.1 support, improved type annotations
- **0.115.0+ (2025)**: Refined WebSocket handling, improved error responses

The project has deliberately stayed at 0.x versioning, though it has been production-ready and stable for years. Sebastian Ramirez has stated that a 1.0 release is planned once certain API stabilization goals are met.
