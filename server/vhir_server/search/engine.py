"""Search query builder — maps VHIR query params to SQLAlchemy + JSONB predicates."""
from __future__ import annotations

from typing import Any

from sqlalchemy import Table, func, select
from sqlalchemy.sql import Select


# Per-resource search parameter definitions.
# Format: {param_name: (kind, jsonb_path)}
# kind: "string" | "token" | "date" | "reference"
_SEARCH_PARAMS: dict[str, dict[str, tuple[str, str]]] = {
    "Animal": {
        "name":        ("string",    "name"),
        "species":     ("token",     "species"),
        "breed":       ("string",    "breed"),
        "sex":         ("token",     "sex"),
        "neuterStatus":("token",     "neuterStatus"),
        "birthDate":   ("date",      "birthDate"),
        "deceased":    ("token",     "deceased"),
        "identifier":  ("identifier","identifiers"),
        "_id":         ("token",     "id"),
    },
    "Owner": {
        "name":        ("string",    "name"),
        "active":      ("token",     "active"),
        "_id":         ("token",     "id"),
    },
    "Practitioner": {
        "name":        ("string",    "name"),
        "active":      ("token",     "active"),
        "_id":         ("token",     "id"),
    },
    "PractitionerRole": {
        "role":         ("token",    "role"),
        "practitioner": ("reference","practitioner"),
        "organization": ("reference","organization"),
        "active":       ("token",    "active"),
        "_id":          ("token",    "id"),
    },
    "Organization": {
        "name":  ("string", "name"),
        "type":  ("token",  "type"),
        "active":("token",  "active"),
        "_id":   ("token",  "id"),
    },
    "Encounter": {
        "status":  ("token",     "status"),
        "class":   ("token",     "class"),
        "subject": ("reference", "subject"),
        "date":    ("date",      "period"),
        "_id":     ("token",     "id"),
    },
    "Observation": {
        "status":   ("token",    "status"),
        "category": ("token",    "category"),
        "code":     ("token",    "code"),
        "subject":  ("reference","subject"),
        "encounter":("reference","encounter"),
        "_id":      ("token",    "id"),
    },
    "Condition": {
        "status":   ("token",    "status"),
        "code":     ("token",    "code"),
        "subject":  ("reference","subject"),
        "encounter":("reference","encounter"),
        "_id":      ("token",    "id"),
    },
    "MedicationRequest": {
        "status":    ("token",    "status"),
        "intent":    ("token",    "intent"),
        "subject":   ("reference","subject"),
        "encounter": ("reference","encounter"),
        "vfd":       ("token",    "vfd"),
        "_id":       ("token",    "id"),
    },
}

_DEFAULT_LIMIT = 20
_MAX_LIMIT = 200


def build_query(table: Table, raw_params: dict[str, Any]) -> tuple[Select, Select]:
    """Return (data_query, count_query) from raw query parameters."""
    resource_type = table.name.replace("_", " ").title().replace(" ", "")
    # Normalize table name to resource type
    _name_map = {
        "animal": "Animal", "owner": "Owner", "practitioner": "Practitioner",
        "practitioner_role": "PractitionerRole", "organization": "Organization",
        "encounter": "Encounter", "observation": "Observation",
        "condition": "Condition", "medication_request": "MedicationRequest",
    }
    resource_type = _name_map.get(table.name, resource_type)
    param_defs = _SEARCH_PARAMS.get(resource_type, {})

    # Pagination
    limit = min(int(raw_params.get("_count", _DEFAULT_LIMIT)), _MAX_LIMIT)
    offset = int(raw_params.get("_offset", 0))

    # Start with base query (not deleted)
    base = table.c.body
    conditions = [table.c.deleted == False]  # noqa: E712

    for key, raw_value in raw_params.items():
        if key.startswith("_") and key not in ("_id",):
            continue
        if key not in param_defs:
            continue

        kind, path = param_defs[key]
        values = [v.strip() for v in str(raw_value).split(",")]

        if kind == "string":
            # Case-insensitive prefix match for any OR value
            or_conds = [
                func.lower(base[path].astext).startswith(v.lower())
                for v in values
            ]
            conditions.append(_or_combine(or_conds))

        elif kind == "token":
            or_conds = [base[path].astext == v for v in values]
            conditions.append(_or_combine(or_conds))

        elif kind == "date":
            # Prefix match on date strings (e.g. ge2020-01-01)
            for v in values:
                if v.startswith("ge"):
                    conditions.append(base[path].astext >= v[2:])
                elif v.startswith("le"):
                    conditions.append(base[path].astext <= v[2:])
                elif v.startswith("gt"):
                    conditions.append(base[path].astext > v[2:])
                elif v.startswith("lt"):
                    conditions.append(base[path].astext < v[2:])
                else:
                    conditions.append(base[path].astext.startswith(v))

        elif kind == "reference":
            or_conds = [base[path]["ref"].astext == v for v in values]
            conditions.append(_or_combine(or_conds))

        elif kind == "identifier":
            # Search inside identifiers array for matching value or type|value
            for v in values:
                if "|" in v:
                    id_type, id_value = v.split("|", 1)
                    conditions.append(
                        base[path].contains([{"type": id_type, "value": id_value}])
                    )
                else:
                    conditions.append(base[path].contains([{"value": v}]))

    stmt = (
        select(table)
        .where(*conditions)
        .order_by(table.c.last_updated.desc())
        .limit(limit)
        .offset(offset)
    )
    count_stmt = (
        select(func.count())
        .select_from(table)
        .where(*conditions)
    )
    return stmt, count_stmt


def _or_combine(conds: list):
    from sqlalchemy import or_
    if len(conds) == 1:
        return conds[0]
    return or_(*conds)
