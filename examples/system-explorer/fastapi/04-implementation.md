# Implementation Patterns

<!-- level:beginner -->
## Common Patterns for Everyday Use

### CRUD Operations

The most common pattern in API development is CRUD (Create, Read, Update, Delete). Here is a complete example:

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI()

# --- Models ---

class BookCreate(BaseModel):
    title: str
    author: str
    year: int

class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    year: int | None = None

class BookResponse(BookCreate):
    id: int

# --- In-memory storage (use a database in production) ---

books_db: dict[int, dict] = {}
next_id = 1

# --- Routes ---

@app.post("/books/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate):
    global next_id
    book_data = {"id": next_id, **book.model_dump()}
    books_db[next_id] = book_data
    next_id += 1
    return book_data

@app.get("/books/", response_model=list[BookResponse])
def list_books(skip: int = 0, limit: int = 10):
    all_books = list(books_db.values())
    return all_books[skip : skip + limit]

@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: int):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    return books_db[book_id]

@app.patch("/books/{book_id}", response_model=BookResponse)
def update_book(book_id: int, book_update: BookUpdate):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    stored = books_db[book_id]
    update_data = book_update.model_dump(exclude_unset=True)
    stored.update(update_data)
    return stored

@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    del books_db[book_id]
```

### File Uploads

```python
from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.post("/upload/")
async def upload_file(file: UploadFile):
    contents = await file.read()
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents),
    }

@app.post("/upload-multiple/")
async def upload_multiple(files: list[UploadFile]):
    return [{"filename": f.filename, "size": f.size} for f in files]
```

### Form Data

```python
from fastapi import FastAPI, Form

app = FastAPI()

@app.post("/login/")
def login(username: str = Form(...), password: str = Form(...)):
    # In production, verify credentials against database
    return {"username": username}
```

### Returning HTML

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/page/{page_name}", response_class=HTMLResponse)
def get_page(request: Request, page_name: str):
    return templates.TemplateResponse(
        "page.html",
        {"request": request, "page_name": page_name},
    )
```

<!-- level:intermediate -->
## Production Patterns

### Dependency Injection for Database Sessions

The most common DI pattern is database session management:

```python
from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# Create a reusable type alias
DbSession = Annotated[AsyncSession, Depends(get_db)]

# Use in any route
@app.get("/users/")
async def list_users(db: DbSession):
    result = await db.execute(select(User))
    return result.scalars().all()
```

### Authentication with OAuth2 + JWT

```python
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

app = FastAPI()

# Configuration
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    email: str

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_from_db(username)
    if user is None:
        raise credentials_exception
    return user

# Reusable dependency type
CurrentUser = Annotated[User, Depends(get_current_user)]

@app.post("/token", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: CurrentUser):
    return current_user
```

### CORS Configuration

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",     # React dev server
        "https://myapp.example.com", # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],  # Custom headers visible to browser
)
```

### Pagination Pattern

```python
from typing import Annotated, Generic, TypeVar
from fastapi import Depends, Query
from pydantic import BaseModel

T = TypeVar("T")

class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 20

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int

def get_pagination(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)

Pagination = Annotated[PaginationParams, Depends(get_pagination)]

@app.get("/items/", response_model=PaginatedResponse[ItemResponse])
async def list_items(pagination: Pagination, db: DbSession):
    total = await db.scalar(select(func.count(Item.id)))
    items = await db.scalars(
        select(Item).offset(pagination.skip).limit(pagination.limit)
    )
    return PaginatedResponse(
        items=items.all(),
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )
```

### Rate Limiting with Dependencies

```python
from fastapi import Depends, HTTPException, Request
import time

# Simple in-memory rate limiter (use Redis in production)
rate_limit_store: dict[str, list[float]] = {}

async def rate_limiter(request: Request, limit: int = 60, window: int = 60):
    client_ip = request.client.host
    now = time.time()

    if client_ip not in rate_limit_store:
        rate_limit_store[client_ip] = []

    # Remove expired timestamps
    rate_limit_store[client_ip] = [
        t for t in rate_limit_store[client_ip] if t > now - window
    ]

    if len(rate_limit_store[client_ip]) >= limit:
        raise HTTPException(
            status_code=429,
            detail="Too many requests",
            headers={"Retry-After": str(window)},
        )

    rate_limit_store[client_ip].append(now)

@app.get("/api/data", dependencies=[Depends(rate_limiter)])
async def get_data():
    return {"data": "Here you go"}
```

<!-- level:advanced -->
## Advanced Implementation Patterns

### Repository Pattern with Generic Types

```python
from typing import Generic, TypeVar, Type
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: int) -> ModelType | None:
        return await self.db.get(self.model, id)

    async def get_multi(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        result = await self.db.scalars(
            select(self.model).offset(skip).limit(limit)
        )
        return result.all()

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        db_obj = self.model(**obj_in.model_dump())
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, id: int, obj_in: UpdateSchemaType) -> ModelType | None:
        db_obj = await self.get(id)
        if db_obj is None:
            return None
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: int) -> bool:
        db_obj = await self.get(id)
        if db_obj is None:
            return False
        await self.db.delete(db_obj)
        return True

# Usage
class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    pass

async def get_user_repo(db: DbSession) -> UserRepository:
    return UserRepository(User, db)

UserRepo = Annotated[UserRepository, Depends(get_user_repo)]

@app.get("/users/{user_id}")
async def get_user(user_id: int, repo: UserRepo):
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404)
    return user
```

### Custom Middleware with State

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
import prometheus_client

REQUEST_COUNT = prometheus_client.Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_DURATION = prometheus_client.Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start_time

        REQUEST_COUNT.labels(
            method=request.method,
            path=request.url.path,
            status=response.status_code,
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method,
            path=request.url.path,
        ).observe(duration)

        return response

app.add_middleware(PrometheusMiddleware)
```

### Dependency Override for Testing

FastAPI's DI system enables clean testing without monkey-patching:

```python
# app/dependencies.py
async def get_db():
    async with SessionLocal() as session:
        yield session

async def get_current_user(token: str = Depends(oauth2_scheme)):
    return await verify_token(token)

# tests/conftest.py
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.dependencies import get_db, get_current_user

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

async def override_get_current_user():
    return User(id=1, username="testuser", email="test@example.com")

@pytest.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
```

### Multi-Tenancy Pattern

```python
from fastapi import Depends, Header, HTTPException

async def get_tenant(x_tenant_id: str = Header(...)):
    tenant = await load_tenant(x_tenant_id)
    if not tenant:
        raise HTTPException(status_code=403, detail="Invalid tenant")
    return tenant

async def get_tenant_db(tenant=Depends(get_tenant)):
    engine = get_engine_for_tenant(tenant.db_url)
    async with async_sessionmaker(engine)() as session:
        yield session

TenantDb = Annotated[AsyncSession, Depends(get_tenant_db)]

@app.get("/data")
async def get_data(db: TenantDb):
    # This query runs against the tenant-specific database
    return await db.scalars(select(Data)).all()
```

### API Versioning

```python
from fastapi import FastAPI, APIRouter

app = FastAPI()

# Version 1
v1_router = APIRouter(prefix="/api/v1")

@v1_router.get("/items/")
def list_items_v1():
    return [{"id": 1, "name": "Widget"}]

# Version 2 with different response shape
v2_router = APIRouter(prefix="/api/v2")

@v2_router.get("/items/")
def list_items_v2():
    return {"data": [{"id": 1, "name": "Widget"}], "meta": {"total": 1}}

app.include_router(v1_router, tags=["v1"])
app.include_router(v2_router, tags=["v2"])
```
