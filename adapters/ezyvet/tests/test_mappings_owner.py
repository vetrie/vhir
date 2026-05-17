"""Unit tests for Owner (Contact) mapping functions."""
from vhir_adapter_ezyvet.mappings.owner import contact_to_vhir, vhir_to_contact


def _ez_contact(**field_overrides):
    return {
        "id": "456",
        "fields": {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "phone": "0412345678",
            "mobile": "0487654321",
            "address": "123 Main St",
            "city": "Sydney",
            "state": "NSW",
            "post_code": "2000",
            "country": "Australia",
            "active": 1,
            **field_overrides,
        },
    }


def test_contact_to_vhir_name():
    result = contact_to_vhir(_ez_contact())
    assert result["name"]["given"] == "Jane"
    assert result["name"]["family"] == "Smith"
    assert result["name"]["full"] == "Jane Smith"


def test_contact_to_vhir_telecom():
    result = contact_to_vhir(_ez_contact())
    systems = [t["system"] for t in result["telecom"]]
    assert "email" in systems
    assert "phone" in systems


def test_contact_to_vhir_address():
    result = contact_to_vhir(_ez_contact())
    addr = result["address"]
    assert addr["city"] == "Sydney"
    assert addr["state"] == "NSW"
    assert addr["postalCode"] == "2000"
    assert "123 Main St" in addr["line"]


def test_contact_to_vhir_identifier():
    result = contact_to_vhir(_ez_contact())
    assert any(i["type"] == "ezyvet-id" and i["value"] == "456" for i in result["identifiers"])


def test_contact_to_vhir_active():
    result = contact_to_vhir(_ez_contact(active=0))
    assert result["active"] is False


def test_contact_to_vhir_organization_type():
    result = contact_to_vhir(_ez_contact(is_company=True))
    assert result["ownerType"] == "organization"


def test_vhir_to_contact_roundtrip():
    vhir = {
        "name": {"given": "John", "family": "Doe"},
        "telecom": [
            {"system": "email", "value": "john@example.com"},
            {"system": "phone", "value": "0411111111", "use": "mobile"},
        ],
        "address": {
            "line": ["5 Oak Ave", "Unit 3"],
            "city": "Melbourne",
            "state": "VIC",
            "postalCode": "3000",
            "country": "Australia",
        },
    }
    payload = vhir_to_contact(vhir)
    f = payload["fields"]
    assert f["first_name"] == "John"
    assert f["last_name"] == "Doe"
    assert f["email"] == "john@example.com"
    assert f["mobile"] == "0411111111"
    assert f["address"] == "5 Oak Ave"
    assert f["address2"] == "Unit 3"
    assert f["city"] == "Melbourne"


def test_vhir_to_contact_minimal():
    payload = vhir_to_contact({"name": {"family": "Solo"}})
    assert payload["fields"]["last_name"] == "Solo"
