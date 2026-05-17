"""ezyVet Product/Prescription ↔ VHIR MedicationRequest + MedicationDispense mapping."""
from __future__ import annotations

from typing import Any


def prescription_to_medication_request(ez: dict[str, Any]) -> dict[str, Any]:
    """Map an ezyVet Prescription to a VHIR MedicationRequestCreate payload."""
    f = ez.get("fields", {})

    animal_id = f.get("animal_id")
    consultation_id = f.get("consultation_id")
    vet_id = f.get("vet_id") or (f.get("vet", {}) or {}).get("id")

    product = f.get("product") or {}
    product_name = product.get("name") if isinstance(product, dict) else f.get("product_name", "")
    product_code = str(product.get("id", "")) if isinstance(product, dict) else f.get("product_id", "")

    qty_raw = f.get("quantity") or f.get("dispensed_quantity")
    qty: float | None = None
    try:
        qty = float(qty_raw) if qty_raw not in (None, "") else None
    except (TypeError, ValueError):
        pass

    unit = f.get("unit") or f.get("dispensing_unit") or "unit"

    status_raw = str(f.get("prescription_status_id", "") or "").lower()
    status = "active" if status_raw in ("", "1", "active") else "completed"

    dosage: dict[str, Any] = {}
    if f.get("dosage_instruction"):
        dosage["text"] = f["dosage_instruction"]
    if qty is not None:
        dosage["doseQuantity"] = {"value": qty, "unit": unit}
    if f.get("frequency"):
        dosage["timing"] = {"code": f["frequency"]}

    return {
        "resourceType": "MedicationRequest",
        "status": status,
        "intent": "order",
        "subject": {"ref": f"Animal/{animal_id}"} if animal_id else {"ref": "Animal/unknown"},
        "encounter": {"ref": f"Encounter/{consultation_id}"} if consultation_id else None,
        "requester": {"ref": f"Practitioner/{vet_id}"} if vet_id else None,
        "medication": {
            "name": product_name,
            "code": product_code,
            "system": "https://api.ezyvet.com/product",
        },
        "dosageInstruction": [dosage] if dosage else [],
        "authoredOn": _isodate(f.get("date") or f.get("created_at")),
        "identifiers": [
            {"type": "ezyvet-id", "system": "https://api.ezyvet.com", "value": str(ez["id"])}
        ],
        "extensions": {"ezyvet_id": str(ez["id"])},
    }


def dispense_item_to_medication_dispense(ez: dict[str, Any]) -> dict[str, Any]:
    """Map an ezyVet dispensing item/invoice line to a VHIR MedicationDispenseCreate payload."""
    f = ez.get("fields", {})

    animal_id = f.get("animal_id")
    consultation_id = f.get("consultation_id")
    vet_id = f.get("vet_id") or (f.get("vet", {}) or {}).get("id")
    prescription_id = f.get("prescription_id")

    product = f.get("product") or {}
    product_name = product.get("name") if isinstance(product, dict) else f.get("product_name", "")
    product_code = str(product.get("id", "")) if isinstance(product, dict) else f.get("product_id", "")

    qty_raw = f.get("quantity") or f.get("dispensed_quantity")
    qty: float | None = None
    try:
        qty = float(qty_raw) if qty_raw not in (None, "") else None
    except (TypeError, ValueError):
        pass

    unit = f.get("unit") or "unit"
    lot = f.get("batch_number") or f.get("lot_number") or None
    expiry = _isodate(f.get("expiry_date"))

    # APVMA/FDA withdrawal period (days) — stored in product custom field
    withdrawal_days_raw = (
        f.get("withholding_period") or f.get("withdrawal_period_days")
    )
    withdrawal_days: int | None = None
    try:
        withdrawal_days = int(withdrawal_days_raw) if withdrawal_days_raw else None
    except (TypeError, ValueError):
        pass

    return {
        "resourceType": "MedicationDispense",
        "status": "completed",
        "subject": {"ref": f"Animal/{animal_id}"} if animal_id else {"ref": "Animal/unknown"},
        "encounter": {"ref": f"Encounter/{consultation_id}"} if consultation_id else None,
        "performer": [{"ref": f"Practitioner/{vet_id}"}] if vet_id else [],
        "authorizingPrescription": [{"ref": f"MedicationRequest/{prescription_id}"}] if prescription_id else [],
        "medication": {
            "name": product_name,
            "code": product_code,
            "system": "https://api.ezyvet.com/product",
        },
        "quantity": {"value": qty, "unit": unit} if qty is not None else None,
        "whenHandedOver": _isodate(f.get("date") or f.get("dispensed_date")),
        "lotNumber": lot,
        "expirationDate": expiry,
        "identifiers": [
            {"type": "ezyvet-id", "system": "https://api.ezyvet.com", "value": str(ez["id"])}
        ],
        "extensions": {
            "ezyvet_id": str(ez["id"]),
            **({"withdrawal_period_days": withdrawal_days} if withdrawal_days else {}),
        },
    }


def _isodate(val: Any) -> str | None:
    if not val:
        return None
    s = str(val).strip()
    if not s or s == "0000-00-00":
        return None
    if s.isdigit():
        import datetime
        return datetime.date.fromtimestamp(int(s)).isoformat()
    return s[:10]
