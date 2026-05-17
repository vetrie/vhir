"""Unit tests for Immunization (Vaccination) mapping."""
from vhir_adapter_ezyvet.mappings.immunization import vaccination_to_vhir


def _ez_vaccination(**field_overrides):
    return {
        "id": "200",
        "fields": {
            "animal_id": "101",
            "vet_id": "10",
            "product": {"id": "70", "name": "Rabies 3yr"},
            "date": "2024-03-15",
            "batch_number": "BATCH001",
            "expiry_date": "2026-01-31",
            "next_due_date": "2027-03-15",
            "route_of_administration": "Subcutaneous",
            "site": "Left flank",
            **field_overrides,
        },
    }


def test_vaccination_basic():
    result = vaccination_to_vhir(_ez_vaccination())
    assert result["resourceType"] == "Immunization"
    assert result["status"] == "completed"
    assert result["subject"]["ref"] == "Animal/101"


def test_vaccination_vaccine_code():
    result = vaccination_to_vhir(_ez_vaccination())
    assert result["vaccineCode"]["code"] == "14"  # CVX for rabies
    assert result["vaccineCode"]["display"] == "Rabies 3yr"


def test_vaccination_lot_and_expiry():
    result = vaccination_to_vhir(_ez_vaccination())
    assert result["lotNumber"] == "BATCH001"
    assert result["expirationDate"] == "2026-01-31"


def test_vaccination_next_due():
    result = vaccination_to_vhir(_ez_vaccination())
    assert result["nextDue"] == "2027-03-15"


def test_vaccination_route():
    result = vaccination_to_vhir(_ez_vaccination())
    assert result["route"] == "subcutaneous"


def test_vaccination_site():
    result = vaccination_to_vhir(_ez_vaccination())
    assert result["site"] == "Left flank"


def test_vaccination_performer():
    result = vaccination_to_vhir(_ez_vaccination())
    assert any("Practitioner/10" in p["ref"] for p in result["performer"])


def test_vaccination_unknown_vaccine():
    result = vaccination_to_vhir(_ez_vaccination(**{"product": {"id": "99", "name": "MysterVax"}}))
    # Should fall back to product code
    assert result["vaccineCode"]["code"] == "99"


def test_vaccination_identifier():
    result = vaccination_to_vhir(_ez_vaccination())
    assert any(i["value"] == "200" for i in result.get("identifiers", []))
