"""Pytest fixtures for VHIR server tests."""
import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from vhir_server.main import app
from vhir_server.storage.database import get_db
from vhir_server.storage.tables import metadata

_TEST_DB_URL = os.environ.get(
    "VHIR_TEST_DATABASE_URL",
    "postgresql+asyncpg://vhir:vhir@127.0.0.1:5432/vhir_test",
)


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(_TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_engine):
    """Each test gets a fresh AsyncClient backed by the shared schema."""
    SessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async def override_get_db():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
