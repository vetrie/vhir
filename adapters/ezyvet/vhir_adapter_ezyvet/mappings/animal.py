"""ezyVet Animal ↔ VHIR Animal mapping."""
from __future__ import annotations

from typing import Any

_SPECIES_MAP: dict[str, str] = {
    "canine": "canine",
    "feline": "feline",
    "equine": "equine",
    "bovine": "bovine",
    "ovine": "ovine",
    "caprine": "caprine",
    "porcine": "porcine",
    "avian": "avian",
    "rabbit": "lagomorph",
    "lagomorph": "lagomorph",
    "reptile": "reptile",
    "fish": "fish",
    "exotic": "exotic",
    "other": "other",
}

_SEX_MAP: dict[str, str] = {
    "male entire": "male",
    "male": "male",
    "female entire": "female",
    "female": "female",
    "male neutered": "neutered-male",
    "castrated": "neutered-male",
    "female spayed": "spayed-female",
    "desexed female": "spayed-female",
    "unknown": "unknown",
}


def _norm_species(raw: str) -> str:
    key = raw.lower().strip()
    return _SPECIES_MAP.get(key, "other")


def _norm_sex(raw: str) -> str:
    key = raw.lower().strip()
    return _SEX_MAP.get(key, "unknown")


def animal_to_vhir(ez: dict[str, Any]) -> dict[str, Any]:
    """Map an ezyVet Animal object to a VHIR AnimalCreate payload."""
    f = ez.get("fields", {})

    species_raw = _nested_name(f.get("species_id") or f.get("species", {}))
    sex_raw = _nested_name(f.get("sex_id") or f.get("sex", {}))
    breed_raw = _nested_name(f.get("breed_id") or f.get("breed", {}))

    identifiers: list[dict[str, Any]] = [
        {"type": "ezyvet-id", "system": "https://api.ezyvet.com", "value": str(ez["id"])}
    ]
    microchip = f.get("microchip")
    if microchip:
        identifiers.append({"type": "microchip", "value": str(microchip)})

    owners: list[dict[str, Any]] = []
    contact_id = f.get("contact_id") or f.get("owner_id")
    if contact_id:
        owners.append({"ref": f"Owner/{contact_id}", "role": "owner"})

    weight_raw = f.get("weight")
    weight_kg: float | None = None
    try:
        weight_kg = float(weight_raw) if weight_raw not in (None, "", "0") else None
    except (TypeError, ValueError):
        pass

    return {
        "resourceType": "Animal",
        "name": f.get("name") or f.get("animal_name"),
        "species": _norm_species(species_raw) if species_raw else "other",
        "breed": breed_raw or None,
        "sex": _norm_sex(sex_raw) if sex_raw else None,
        "birthDate": _isodate(f.get("date_of_birth")),
        "deceased": bool(int(f.get("is_deceased", 0) or 0)),
        "deathDate": _isodate(f.get("date_of_death")),
        "color": f.get("color") or None,
        "weightKg": weight_kg,
        "identifiers": identifiers,
        "owners": owners,
        "note": f.get("notes") or None,
        "extensions": {"ezyvet_id": str(ez["id"])},
    }


def vhir_to_animal(vhir: dict[str, Any]) -> dict[str, Any]:
    """Map a VHIR Animal to a minimal ezyVet Animal update payload."""
    _SPECIES_REVERSE = {v: k.title() for k, v in _SPECIES_MAP.items()}
    _SEX_REVERSE = {
        "male": "Male Entire",
        "female": "Female Entire",
        "neutered-male": "Male Neutered",
        "spayed-female": "Female Spayed",
        "unknown": "Unknown",
    }
    fields: dict[str, Any] = {}
    if vhir.get("name"):
        fields["name"] = vhir["name"]
    if vhir.get("species"):
        fields["species"] = _SPECIES_REVERSE.get(vhir["species"], vhir["species"].title())
    if vhir.get("sex"):
        fields["sex"] = _SEX_REVERSE.get(vhir["sex"], vhir["sex"].title())
    if vhir.get("birthDate"):
        fields["date_of_birth"] = vhir["birthDate"]
    if vhir.get("breed"):
        fields["breed"] = vhir["breed"]
    if vhir.get("color"):
        fields["color"] = vhir["color"]
    if vhir.get("weightKg") is not None:
        fields["weight"] = str(vhir["weightKg"])
    return {"fields": fields}


def _nested_name(val: Any) -> str:
    if isinstance(val, dict):
        return str(val.get("name", ""))
    return str(val) if val else ""


def _isodate(val: Any) -> str | None:
    if not val:
        return None
    s = str(val).strip()
    if not s or s == "0000-00-00":
        return None
    # ezyVet returns dates as YYYY-MM-DD or Unix timestamps
    if s.isdigit():
        n = int(s)
        if n == 0:
            return None
        import datetime
        return datetime.date.fromtimestamp(n).isoformat()
    return s[:10]
