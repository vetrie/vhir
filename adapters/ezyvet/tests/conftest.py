"""Shared test fixtures for the ezyVet adapter test suite."""
import pytest
import respx
import httpx


@pytest.fixture
def ezyvet_base_url() -> str:
    return "https://api.ezyvet.com"


@pytest.fixture
def mock_ezyvet(ezyvet_base_url: str):
    """respx router mocking the ezyVet API."""
    with respx.mock(base_url=ezyvet_base_url, assert_all_called=False) as mock:
        # Token endpoint always returns a valid token
        mock.post("/v1/oauth/access_token").mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "test-token", "expires_in": 3600},
            )
        )
        yield mock


@pytest.fixture
def mock_vhir():
    """respx router mocking the VHIR server."""
    with respx.mock(base_url="http://localhost:8000", assert_all_called=False) as mock:
        yield mock
