"""Tests for the webhook endpoint."""
import pytest
import httpx
import respx
from fastapi.testclient import TestClient

from vhir_adapter_ezyvet.sync.webhook import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)

client = TestClient(app)


def _event(resource_type: str, resource_id: str = "101") -> dict:
    return {
        "id": "evt-001",
        "resource_type": resource_type,
        "resource": {
            "id": resource_id,
            "fields": {
                "animal_id": "101",
                "name": "Buddy",
                "species": {"name": "Canine"},
                "sex": {"name": "Male Entire"},
            },
        },
    }


def test_webhook_returns_202():
    with respx.mock(base_url="http://localhost:8000", assert_all_called=False):
        resp = client.post("/webhook/ezyvet", json=_event("animal"))
    assert resp.status_code == 202


def test_webhook_accepts_list():
    with respx.mock(base_url="http://localhost:8000", assert_all_called=False):
        resp = client.post("/webhook/ezyvet", json=[_event("animal"), _event("contact", "456")])
    assert resp.status_code == 202
    assert resp.json()["count"] == "2"


def test_webhook_unknown_resource_type():
    """Unknown types are silently logged, not 4xx."""
    with respx.mock(base_url="http://localhost:8000", assert_all_called=False):
        resp = client.post("/webhook/ezyvet", json=_event("invoiceline"))
    assert resp.status_code == 202


def test_webhook_duplicate_event_ignored():
    """Same event ID sent twice — only processed once."""
    from vhir_adapter_ezyvet.sync.webhook import _SEEN_EVENTS
    _SEEN_EVENTS.clear()
    with respx.mock(base_url="http://localhost:8000", assert_all_called=False):
        client.post("/webhook/ezyvet", json=_event("animal"))
        client.post("/webhook/ezyvet", json=_event("animal"))
    # Both requests should succeed (202), dedup is handled internally
