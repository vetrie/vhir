"""Adapter service entry point — webhook server + background poll loop."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from vhir_adapter_ezyvet.sync.daemon import run_poll_loop
from vhir_adapter_ezyvet.sync.webhook import router as webhook_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    task = asyncio.create_task(run_poll_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="VHIR ezyVet Adapter",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(webhook_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
