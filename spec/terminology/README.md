# VHIR Terminology Bindings

This document defines the coding systems bound to VHIR resource fields, with guidance on how to use and extend them.

Machine-readable version: [`bindings.json`](bindings.json)

---

## Terminology Systems

| ID | Name | System URI | Purpose |
|----|------|-----------|---------|
| `aaha-diagnostic-terms` | AAHA Diagnostic Terms | `urn:aaha:diagnostic-terms` | Companion-animal diagnoses (dogs, cats, ferrets, rabbits) |
| `snomed-ct-vet` | SNOMED CT Veterinary Extension | `http://snomed.info/sct` | Procedures (surgery, dental, imaging); secondary for conditions |
| `venom` | VeNom Coding Project | `http://venom-project.org` | Cross-species clinical terms; fills gaps for exotics, equine, food animals |
| `ucum` | UCUM | `http://unitsofmeasure.org` | Units for all quantity fields (dose, observations, volumes) |
| `ndf-rt` | NDF-RT | `http://hl7.org/fhir/ndfrt` | Pharmacological drug class codes for medication resources |
| `vhir-vaccine-codes` | VHIR Vaccine Codes | `https://vhir.dev/codesystems/vaccine-codes` | Vaccine identifiers (AAHA/AAFP/AAEP categories); see [`spec/valuesets/vaccine_codes.json`](../valuesets/vaccine_codes.json) |
| `loinc` | LOINC | `http://loinc.org` | Optional secondary for Observation codes where a veterinary LOINC term exists |

### Binding strength definitions

| Strength | Meaning |
|----------|---------|
| **required** | Implementations MUST use a code from the specified value set. |
| **preferred** | Implementations SHOULD use a code from the specified value set; deviation must be documented. |
| **example** | Implementations MAY use a code from the specified value set; free text is also acceptable. |

---

## Binding Table

| Resource | Field | Strength | Preferred System | Fallback Systems | Value Set URL |
|----------|-------|----------|-----------------|-----------------|---------------|
| Condition | `code` | preferred | AAHA Diagnostic Terms | VeNom, SNOMED CT-VET | `https://vhir.dev/valuesets/aaha-diagnostic-terms` |
| Procedure | `code` | preferred | SNOMED CT-VET | VeNom | `https://vhir.dev/valuesets/snomed-ct-vet-procedures` |
| Observation | `code` | preferred | VHIR Vitals Catalog | LOINC | `https://vhir.dev/valuesets/vhir-vitals` |
| Observation | `valueQuantity.system` | **required** | UCUM | — | `https://vhir.dev/valuesets/ucum-units` |
| Observation | `component[].valueQuantity.system` | **required** | UCUM | — | `https://vhir.dev/valuesets/ucum-units` |
| MedicationRequest | `medication.system` | example | NDF-RT | — | `https://vhir.dev/valuesets/ndf-rt-drug-classes` |
| MedicationRequest | `dosageInstruction[].doseQuantity.system` | **required** | UCUM | — | `https://vhir.dev/valuesets/ucum-units` |
| MedicationAdministration | `medication.system` | example | NDF-RT | — | `https://vhir.dev/valuesets/ndf-rt-drug-classes` |
| MedicationDispense | `medication.system` | example | NDF-RT | — | `https://vhir.dev/valuesets/ndf-rt-drug-classes` |
| Immunization | `vaccineCode` | preferred | VHIR Vaccine Codes | — | `https://vhir.dev/valuesets/vaccine-codes` |
| Immunization | `doseQuantity.system` | **required** | UCUM | — | `https://vhir.dev/valuesets/ucum-units` |

---

## Examples

### Condition — AAHA Diagnostic Terms

```json
{
  "resourceType": "Condition",
  "code": {
    "system": "urn:aaha:diagnostic-terms",
    "code": "DX-OM-001",
    "display": "Otitis media"
  }
}
```

### Condition — VeNom (exotic / equine fallback)

```json
{
  "resourceType": "Condition",
  "code": {
    "system": "http://venom-project.org",
    "code": "VeNom:0000131",
    "display": "Laminitis"
  }
}
```

### Procedure — SNOMED CT-VET

```json
{
  "resourceType": "Procedure",
  "code": {
    "system": "http://snomed.info/sct",
    "code": "180227004",
    "display": "Surgical castration of male animal"
  }
}
```

### Observation — UCUM unit (required)

```json
{
  "resourceType": "Observation",
  "code": { "system": "https://vhir.dev/codesystems/vitals", "code": "body-weight", "display": "Body weight" },
  "valueQuantity": {
    "value": 32.5,
    "unit": "kg",
    "system": "http://unitsofmeasure.org",
    "code": "kg"
  }
}
```

### MedicationRequest — NDF-RT drug class (example)

```json
{
  "resourceType": "MedicationRequest",
  "medication": {
    "name": "Amoxicillin",
    "system": "http://hl7.org/fhir/ndfrt",
    "code": "N0000175503",
    "form": "capsule"
  },
  "dosageInstruction": [{
    "route": "oral",
    "doseQuantity": { "value": 250, "unit": "mg", "system": "http://unitsofmeasure.org", "code": "mg" },
    "frequency": "BID",
    "duration": "10 days"
  }]
}
```

### Immunization — VHIR Vaccine Codes

```json
{
  "resourceType": "Immunization",
  "vaccineCode": {
    "system": "https://vhir.dev/codesystems/vaccine-codes",
    "code": "da2pp",
    "display": "DA2PP (Canine Distemper + Adenovirus-2 + Parvovirus + Parainfluenza)"
  },
  "doseQuantity": {
    "value": 1.0,
    "unit": "mL",
    "system": "http://unitsofmeasure.org",
    "code": "mL"
  }
}
```

---

## Extending with Clinic-Specific Codes

VHIR does not restrict codes to published value sets at the wire level. Practices can introduce proprietary codes using a namespaced URI scheme to prevent collisions:

### Namespace convention

```
urn:clinic:<domain>:<local-code>
```

| Segment | Meaning | Example |
|---------|---------|---------|
| `urn:clinic:` | Fixed prefix for VHIR clinic-specific codes | — |
| `<domain>` | Practice domain or short identifier | `pinevalleyvet` |
| `<local-code>` | Code identifier, unique within the domain | `surg-001` |

**Full example URI:** `urn:clinic:pinevalleyvet:surg-001`

### Usage pattern

```json
{
  "resourceType": "Procedure",
  "code": {
    "system": "urn:clinic:pinevalleyvet",
    "code": "surg-001",
    "display": "Soft-tissue mass removal — facial region",
    "text": "Pine Valley internal billing code for soft-tissue facial mass excision"
  }
}
```

### Rules for clinic-specific codes

1. **Always include `display` or `text`** so the record is self-documenting.
2. **Document the code list** in your implementation's conformance statement or a local JSON file mirroring `spec/valuesets/` format.
3. **Prefer a standard code alongside your local one** when a standard code exists — add a second coding object under an `extensions` key if you need to carry both:

   ```json
   "code": {
     "system": "urn:clinic:pinevalleyvet",
     "code": "surg-001",
     "display": "Soft-tissue mass removal — facial region"
   },
   "extensions": {
     "standardCoding": {
       "system": "http://snomed.info/sct",
       "code": "174432007",
       "display": "Excision of lesion of skin"
     }
   }
   ```

4. **Avoid `urn:clinic:vhir:*`** — that prefix is reserved for future VHIR-project-defined extensions.

### Requesting promotion to the VHIR standard value sets

If a clinic-specific code or an entirely new terminology binding is broadly useful, open a GitHub issue or RFC in the VHIR project. Codes are promoted when at least two independent implementations have adopted them and a standard-body code cannot serve the same purpose.
