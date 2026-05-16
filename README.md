# VHIR — Veterinary Health Interoperability Resources

> A FHIR-inspired, vet-medicine-first interoperability standard. Standalone JSON+REST spec with a reference Python server and adapters for real PIMS systems.

## Why VHIR?

Veterinary medicine has no FHIR equivalent. ~100 fragmented PIMS systems, no shared wire format, and critical workflows — herd treatments, withdrawal periods, microchip lookup, controlled-substance logs — have no common model.

VHIR borrows FHIR's best ideas (resource-oriented REST, JSON-first, extensions, profiles, terminology bindings, OAuth2 scopes) and cuts the regulatory overhead that only exists for human-medicine compliance (HIPAA, Meaningful Use, C-CDA, ICD-10/CPT/RxNorm).

## Spec highlights

- **Animal** (not `Patient`) — mandatory `species`, `breed`, `neuterStatus`, `microchip`
- **Group** — first-class herd/flock support with per-member treatment completion and withdrawal-period tracking
- **Device** — microchip (ISO 11784/11785), livestock EID (USDA 840), wearables (PetPace, Allflex)
- **`$lookup-microchip`** — federated registry query (AAHA broker model, owner PII never exposed)
- **InsuranceClaim** — Trupanion VetDirectPay + Nationwide/Pets Best post-service model
- Terminology bound to AAHA Diagnostic Terms + SNOMED CT-VET + VeNom

## Repo layout

```
spec/           JSON Schemas, resource specs, value sets, OpenAPI
server/         Reference implementation (FastAPI + Postgres)
adapters/       PIMS adapters (ezyVet first)
sdk/            Client SDKs (Python first, generated from OpenAPI)
docs/           Governance, RFCs, walkthroughs
```

## Quick start

```bash
# requires docker + uv
git clone https://github.com/vhir/vhir && cd vhir
cd server && docker compose up -d && uv run uvicorn vhir_server.main:app --reload
```

API explorer: http://localhost:8000/v1/_openapi.json

## Status: M0 (pre-release)

Resources implemented: Animal, Owner, Practitioner, PractitionerRole, Organization, Encounter, Observation, Condition, MedicationRequest.

## License

Code: Apache-2.0 · Spec text: CC-BY-4.0
