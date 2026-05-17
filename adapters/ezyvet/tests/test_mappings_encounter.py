"""Unit tests for Encounter (Consultation) mapping."""
from vhir_adapter_ezyvet.mappings.encounter import encounter_to_vhir


def _ez_consultation(**field_overrides):
    return {
        "id": "789",
        "fields": {
            "animal_id": "101",
            "contact_id": "456",
            "status": {"id": "1", "name": "Active"},
            "date": "2024-03-15",
            "vet": {"id": "10", "name": "Dr. Smith"},
            "reason_for_visit": "Annual checkup",
            **field_overrides,
        },
    }


def test_encounter_to_vhir_basic():
    result = encounter_to_vhir(_ez_consultation())
    assert result["resourceType"] == "Encounter"
    assert result["status"] == "in-progress"
    assert result["subject"]["ref"] == "Animal/101"
    assert result["owner"]["ref"] == "Owner/456"


def test_encounter_to_vhir_practitioners():
    result = encounter_to_vhir(_ez_consultation())
    assert any(p["practitioner"]["ref"] == "Practitioner/10" for p in result["practitioners"])


def test_encounter_to_vhir_period():
    result = encounter_to_vhir(_ez_consultation())
    assert result["period"]["start"] == "2024-03-15"


def test_encounter_to_vhir_reason():
    result = encounter_to_vhir(_ez_consultation())
    assert result["reasonText"] == "Annual checkup"


def test_encounter_to_vhir_closed_status():
    result = encounter_to_vhir(_ez_consultation(**{"status": {"id": "2", "name": "Closed"}}))
    assert result["status"] == "finished"


def test_encounter_to_vhir_cancelled():
    result = encounter_to_vhir(_ez_consultation(**{"status": {"id": "3", "name": "Cancelled"}}))
    assert result["status"] == "cancelled"


def test_encounter_to_vhir_no_animal():
    ez = {"id": "999", "fields": {"status": {"name": "Active"}}}
    result = encounter_to_vhir(ez)
    assert result["subject"]["ref"] == "Animal/unknown"


def test_encounter_to_vhir_identifier():
    result = encounter_to_vhir(_ez_consultation())
    assert any(i["value"] == "789" for i in result.get("identifiers", []))
