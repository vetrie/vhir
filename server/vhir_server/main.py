"""VHIR Reference Server entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from vhir_server.api.animal import router as animal_router
from vhir_server.api.resources import (
    condition_router,
    encounter_router,
    medication_request_router,
    observation_router,
    organization_router,
    owner_router,
    practitioner_role_router,
    practitioner_router,
)
from vhir_server.api.system import router as system_router
from vhir_server.config import settings
from vhir_server.storage.database import engine
from vhir_server.storage.tables import metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="VHIR Reference Server",
    description="Veterinary Health Interoperability Resources — reference implementation",
    version="0.1.0",
    docs_url="/v1/_docs",
    redoc_url="/v1/_redoc",
    openapi_url="/v1/_openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# System routes (no prefix)
app.include_router(system_router)

# Resource routes under /v1
prefix = settings.api_prefix
app.include_router(animal_router,            prefix=prefix)
app.include_router(owner_router,             prefix=prefix)
app.include_router(practitioner_router,      prefix=prefix)
app.include_router(practitioner_role_router, prefix=prefix)
app.include_router(organization_router,      prefix=prefix)
app.include_router(encounter_router,         prefix=prefix)
app.include_router(observation_router,       prefix=prefix)
app.include_router(condition_router,         prefix=prefix)
app.include_router(medication_request_router,prefix=prefix)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": str(exc)},
    )


@app.get("/")
async def root() -> dict:
    return {
        "name": "VHIR Reference Server",
        "version": "0.1.0",
        "docs": f"{settings.server_base_url}/v1/_docs",
        "metadata": f"{settings.server_base_url}/v1/metadata",
    }
