"""Unit tests for Observation (ClinicalNote) mapping."""
from vhir_adapter_ezyvet.mappings.observation import clinical_note_to_vhir


def _ez_note(**field_overrides):
    return {
        "id": "555",
        "fields": {
            "animal_id": "101",
            "consultation_id": "789",
            "title": "Examination findings",
            "description": "Animal presented with mild lethargy.",
            "date": "2024-03-15",
            **field_overrides,
        },
    }


def test_observation_to_vhir_basic():
    result = clinical_note_to_vhir(_ez_note())
    assert result["resourceType"] == "Observation"
    assert result["status"] == "final"
    assert result["subject"]["ref"] == "Animal/101"
    assert result["encounter"]["ref"] == "Encounter/789"


def test_observation_to_vhir_value_string():
    result = clinical_note_to_vhir(_ez_note())
    assert result["valueString"] == "Animal presented with mild lethargy."


def test_observation_to_vhir_code():
    result = clinical_note_to_vhir(_ez_note())
    assert result["code"]["code"] == "clinical-note"
    assert result["code"]["display"] == "Examination findings"


def test_observation_to_vhir_effective_date():
    result = clinical_note_to_vhir(_ez_note())
    assert result["effectiveDateTime"] == "2024-03-15"


def test_observation_to_vhir_no_animal():
    ez = {"id": "666", "fields": {"title": "Note"}}
    result = clinical_note_to_vhir(ez)
    assert result["subject"]["ref"] == "Animal/unknown"
    assert result["encounter"] is None


def test_observation_to_vhir_identifier():
    result = clinical_note_to_vhir(_ez_note())
    assert any(i["value"] == "555" for i in result.get("identifiers", []))


def test_observation_unix_timestamp():
    result = clinical_note_to_vhir(_ez_note(date="1710460800"))
    assert result["effectiveDateTime"] is not None
    assert "2024" in result["effectiveDateTime"]
