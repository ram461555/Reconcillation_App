"""FastAPI application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine, run_lightweight_migrations
from app.routers import auth, ledger, sessions

# Import models so they're registered on Base.metadata before create_all()
from app import models  # noqa: F401

Base.metadata.create_all(bind=engine)
run_lightweight_migrations()

app = FastAPI(title="Reconciliation App API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(ledger.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
