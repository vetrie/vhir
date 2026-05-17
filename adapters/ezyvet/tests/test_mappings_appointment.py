"""Unit tests for Appointment mapping."""
from vhir_adapter_ezyvet.mappings.appointment import appointment_to_vhir, slot_to_vhir


def _ez_appointment(**field_overrides):
    return {
        "id": "600",
        "fields": {
            "animal_id": "101",
            "contact_id": "456",
            "vet_id": "10",
            "status": {"id": "1", "name": "Confirmed"},
            "start_at": "2024-04-01T09:00:00",
            "end_at": "2024-04-01T09:30:00",
            "duration": 30,
            "description": "Annual checkup",
            "resource_id": "5",
            **field_overrides,
        },
    }


def test_appointment_basic():
    result = appointment_to_vhir(_ez_appointment())
    assert result["resourceType"] == "Appointment"
    assert result["status"] == "booked"
    assert result["start"] == "2024-04-01T09:00:00"
    assert result["end"] == "2024-04-01T09:30:00"
    assert result["minutesDuration"] == 30


def test_appointment_participants():
    result = appointment_to_vhir(_ez_appointment())
    refs = [p["actor"]["ref"] for p in result["participants"]]
    assert "Animal/101" in refs
    assert "Owner/456" in refs
    assert "Practitioner/10" in refs


def test_appointment_cancelled_status():
    result = appointment_to_vhir(_ez_appointment(**{"status": {"name": "Cancelled"}}))
    assert result["status"] == "cancelled"


def test_appointment_no_show():
    result = appointment_to_vhir(_ez_appointment(**{"status": {"name": "No Show"}}))
    assert result["status"] == "noshow"


def test_appointment_identifier():
    result = appointment_to_vhir(_ez_appointment())
    assert any(i["value"] == "600" for i in result.get("identifiers", []))


def test_slot_basic():
    ez = {
        "id": "700",
        "fields": {
            "resource_id": "5",
            "start_at": "2024-04-01T08:00:00",
            "end_at": "2024-04-01T09:00:00",
        },
    }
    result = slot_to_vhir(ez)
    assert result["resourceType"] == "Slot"
    assert result["status"] == "free"
    assert result["start"] == "2024-04-01T08:00:00"
    assert result["schedule"]["ref"] == "Schedule/5"


def test_slot_identifier():
    ez = {"id": "700", "fields": {"resource_id": "5", "start_at": None, "end_at": None}}
    result = slot_to_vhir(ez)
    assert any(i["value"] == "700" for i in result.get("identifiers", []))
