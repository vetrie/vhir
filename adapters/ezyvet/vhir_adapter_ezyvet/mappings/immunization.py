"""ezyVet Vaccination ↔ VHIR Immunization mapping."""
from __future__ import annotations

from typing import Any

# Common rabies/core vaccine code lookups (CVX / SNOMED approximations)
_VACCINE_CODE_MAP: dict[str, str] = {
    "rabies": "14",        # CVX 14
    "dhpp": "vhir-dhpp",
    "fvrcp": "vhir-fvrcp",
    "bordetella": "vhir-bordetella",
    "leptospirosis": "vhir-lepto",
    "lyme": "vhir-lyme",
    "influenza": "vhir-flu",
}


def vaccination_to_vhir(ez: dict[str, Any]) -> dict[str, Any]:
    """Map an ezyVet Vaccination record to a VHIR ImmunizationCreate payload."""
    f = ez.get("fields", {})

    animal_id = f.get("animal_id")
    vet_id = f.get("vet_id") or (f.get("vet", {}) or {}).get("id")

    product = f.get("product") or {}
    vaccine_name = (
        product.get("name") if isinstance(product, dict) else f.get("product_name", "")
    ) or ""
    product_code = (
        str(product.get("id", "")) if isinstance(product, dict) else f.get("product_id", "")
    )

    # Try to match a known vaccine code
    vax_code = _vaccine_code_map(vaccine_name) or product_code

    lot_number = f.get("batch_number") or f.get("lot_number") or None
    expiry = _isodate(f.get("expiry_date"))
    due_date = _isodate(f.get("next_due_date") or f.get("booster_due"))

    route_raw = f.get("route_of_administration") or ""
    route = _norm_route(route_raw)

    site_raw = f.get("site") or f.get("injection_site") or ""

    return {
        "resourceType": "Immunization",
        "status": "completed",
        "vaccineCode": {
            "system": "http://hl7.org/fhir/sid/cvx" if vax_code.isdigit() else "http://vhir.org/CodeSystem/vaccine-codes",
            "code": vax_code,
            "display": vaccine_name,
        },
        "subject": {"ref": f"Animal/{animal_id}"} if animal_id else {"ref": "Animal/unknown"},
        "occurrenceDateTime": _isodate(f.get("date") or f.get("vaccination_date")),
        "performer": [{"ref": f"Practitioner/{vet_id}"}] if vet_id else [],
        "lotNumber": lot_number,
        "expirationDate": expiry,
        "nextDue": due_date,
        "route": route or None,
        "site": site_raw or None,
        "identifiers": [
            {"type": "ezyvet-id", "system": "https://api.ezyvet.com", "value": str(ez["id"])}
        ],
        "extensions": {"ezyvet_id": str(ez["id"])},
    }


def _vaccine_code_map(name: str) -> str:
    if not name:
        return ""
    lower = name.lower()
    for k, v in _VACCINE_CODE_MAP.items():
        if k in lower:
            return v
    return ""


def _norm_route(raw: str) -> str:
    r = raw.lower().strip()
    if "subcutaneous" in r or "subcut" in r or "sq" in r:
        return "subcutaneous"
    if "intramuscular" in r or "im" in r:
        return "intramuscular"
    if "intranasal" in r:
        return "intranasal"
    if "oral" in r:
        return "oral"
    return raw or ""


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
