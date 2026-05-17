import pytest
import respx
from vhir_sdk.client import VhirClient

BASE_URL = "http://test.vhir.local"
TOKEN = "test-token"


@pytest.fixture
def mock_api():
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as m:
        yield m


@pytest.fixture
async def client(mock_api):
    async with VhirClient(BASE_URL, token=TOKEN) as c:
        yield c
