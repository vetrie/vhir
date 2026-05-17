"""Unit tests for Medication mapping functions."""
from vhir_adapter_ezyvet.mappings.medication import (
    prescription_to_medication_request,
    dispense_item_to_medication_dispense,
)


def _ez_prescription(**field_overrides):
    return {
        "id": "300",
        "fields": {
            "animal_id": "101",
            "consultation_id": "789",
            "vet_id": "10",
            "product": {"id": "50", "name": "Amoxicillin 250mg"},
            "quantity": "10",
            "unit": "tablet",
            "dosage_instruction": "Give 1 tablet twice daily",
            "date": "2024-03-15",
            **field_overrides,
        },
    }


def _ez_dispense(**field_overrides):
    return {
        "id": "400",
        "fields": {
            "animal_id": "101",
            "consultation_id": "789",
            "vet_id": "10",
            "prescription_id": "300",
            "product": {"id": "50", "name": "Amoxicillin 250mg"},
            "quantity": "10",
            "unit": "tablet",
            "batch_number": "LOT123",
            "expiry_date": "2025-06-30",
            "date": "2024-03-15",
            **field_overrides,
        },
    }


def test_prescription_basic():
    result = prescription_to_medication_request(_ez_prescription())
    assert result["resourceType"] == "MedicationRequest"
    assert result["status"] == "active"
    assert result["subject"]["ref"] == "Animal/101"
    assert result["encounter"]["ref"] == "Encounter/789"
    assert result["requester"]["ref"] == "Practitioner/10"


def test_prescription_medication_info():
    result = prescription_to_medication_request(_ez_prescription())
    assert result["medication"]["name"] == "Amoxicillin 250mg"
    assert result["medication"]["code"] == "50"


def test_prescription_dosage():
    result = prescription_to_medication_request(_ez_prescription())
    dosage = result["dosageInstruction"][0]
    assert "Give 1 tablet" in dosage["text"]
    assert dosage["doseQuantity"]["value"] == 10.0


def test_prescription_identifier():
    result = prescription_to_medication_request(_ez_prescription())
    assert any(i["value"] == "300" for i in result.get("identifiers", []))


def test_dispense_basic():
    result = dispense_item_to_medication_dispense(_ez_dispense())
    assert result["resourceType"] == "MedicationDispense"
    assert result["status"] == "completed"
    assert result["subject"]["ref"] == "Animal/101"


def test_dispense_lot_and_expiry():
    result = dispense_item_to_medication_dispense(_ez_dispense())
    assert result["lotNumber"] == "LOT123"
    assert result["expirationDate"] == "2025-06-30"


def test_dispense_quantity():
    result = dispense_item_to_medication_dispense(_ez_dispense())
    assert result["quantity"]["value"] == 10.0
    assert result["quantity"]["unit"] == "tablet"


def test_dispense_withdrawal_period():
    result = dispense_item_to_medication_dispense(_ez_dispense(withdrawal_period_days="28"))
    assert result["extensions"]["withdrawal_period_days"] == 28


def test_dispense_authorizing_prescription():
    result = dispense_item_to_medication_dispense(_ez_dispense())
    assert any("MedicationRequest/300" in r["ref"] for r in result["authorizingPrescription"])
