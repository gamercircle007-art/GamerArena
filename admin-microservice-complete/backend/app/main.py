from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
import app.models.admin_user  # noqa: F401 — register ORM models
from app.models.base import create_tables
from app.routers import admin, auth
from app.seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    await seed()
    yield


app = FastAPI(
    title="GameConnect Admin API",
    description="Separate admin microservice for GameConnect platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "admin-microservice", "port": settings.PORT}


app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")