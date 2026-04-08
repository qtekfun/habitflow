from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, habits, logs


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Scheduler start/stop will be wired here in a later phase
    yield


app = FastAPI(
    title="HabitFlow API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(habits.router)
app.include_router(logs.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
