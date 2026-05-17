"""ezyVet Contact ↔ VHIR Owner mapping."""
from __future__ import annotations

from typing import Any


def contact_to_vhir(ez: dict[str, Any]) -> dict[str, Any]:
    """Map an ezyVet Contact to a VHIR OwnerCreate payload."""
    f = ez.get("fields", {})

    name: dict[str, Any] = {}
    if f.get("first_name"):
        name["given"] = f["first_name"]
    if f.get("last_name"):
        name["family"] = f["last_name"]
    full = " ".join(filter(None, [f.get("first_name"), f.get("last_name")])).strip()
    if full:
        name["full"] = full

    telecom: list[dict[str, str]] = []
    if f.get("email"):
        telecom.append({"system": "email", "value": f["email"]})
    for ph_key, ph_use in [("phone", "home"), ("mobile", "mobile"), ("work_phone", "work")]:
        if f.get(ph_key):
            telecom.append({"system": "phone", "value": f[ph_key], "use": ph_use})

    address: dict[str, Any] | None = None
    addr_parts = [f.get("address"), f.get("address2")]
    addr_lines = [a for a in addr_parts if a]
    if any([addr_lines, f.get("city"), f.get("state"), f.get("post_code"), f.get("country")]):
        address = {
            "line": addr_lines,
            "city": f.get("city") or None,
            "state": f.get("state") or None,
            "postalCode": f.get("post_code") or None,
            "country": f.get("country") or None,
        }

    return {
        "resourceType": "Owner",
        "name": name or None,
        "ownerType": "individual" if not f.get("is_company") else "organization",
        "telecom": telecom,
        "address": address,
        "identifiers": [
            {"type": "ezyvet-id", "system": "https://api.ezyvet.com", "value": str(ez["id"])}
        ],
        "active": bool(int(f.get("active", 1))),
        "note": f.get("notes") or None,
        "extensions": {"ezyvet_id": str(ez["id"])},
    }


def vhir_to_contact(vhir: dict[str, Any]) -> dict[str, Any]:
    """Map a VHIR Owner to a minimal ezyVet Contact update payload."""
    fields: dict[str, Any] = {}
    name = vhir.get("name") or {}
    if name.get("given"):
        fields["first_name"] = name["given"]
    if name.get("family"):
        fields["last_name"] = name["family"]

    for t in vhir.get("telecom", []):
        if t.get("system") == "email":
            fields["email"] = t["value"]
        elif t.get("system") == "phone":
            use = t.get("use", "home")
            key_map = {"mobile": "mobile", "work": "work_phone", "home": "phone"}
            fields[key_map.get(use, "phone")] = t["value"]

    addr = vhir.get("address") or {}
    if addr.get("line"):
        fields["address"] = addr["line"][0]
        if len(addr["line"]) > 1:
            fields["address2"] = addr["line"][1]
    if addr.get("city"):
        fields["city"] = addr["city"]
    if addr.get("state"):
        fields["state"] = addr["state"]
    if addr.get("postalCode"):
        fields["post_code"] = addr["postalCode"]
    if addr.get("country"):
        fields["country"] = addr["country"]

    return {"fields": fields}
