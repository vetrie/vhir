#!/usr/bin/env bash
# VHIR walkthrough: companion animal GP visit
# Requires: curl, jq, running VHIR server on localhost:8000
set -euo pipefail
BASE="http://localhost:8000/v1"

echo "=== VHIR Companion Animal Visit Walkthrough ==="
echo ""

# 1. Create clinic
echo "[1/7] Creating clinic..."
ORG=$(curl -s -X POST "$BASE/Organization" \
  -H "Content-Type: application/json" \
  -d '{"resourceType":"Organization","name":"Sunshine Vet Clinic","type":"clinic","telecom":[{"system":"phone","value":"+1-555-0100"}]}')
ORG_ID=$(echo "$ORG" | jq -r '.id')
echo "    Organization: $ORG_ID"

# 2. Create veterinarian
echo "[2/7] Creating veterinarian..."
VET=$(curl -s -X POST "$BASE/Practitioner" \
  -H "Content-Type: application/json" \
  -d '{"resourceType":"Practitioner","name":{"given":"Maria","family":"Santos","prefix":"Dr.","suffix":"DVM"},"qualifications":[{"code":"DVM","licenseNumber":"CA-DVM-54321","jurisdiction":"US-CA"}],"deaNumber":"BS1234567"}')
VET_ID=$(echo "$VET" | jq -r '.id')
echo "    Practitioner: $VET_ID"

# 3. Create owner
echo "[3/7] Creating owner..."
OWNER=$(curl -s -X POST "$BASE/Owner" \
  -H "Content-Type: application/json" \
  -d '{"resourceType":"Owner","name":{"given":"Carlos","family":"Reyes"},"telecom":[{"system":"email","value":"carlos@example.com"},{"system":"phone","value":"+1-555-9999","use":"mobile"}]}')
OWNER_ID=$(echo "$OWNER" | jq -r '.id')
echo "    Owner: $OWNER_ID"

# 4. Create animal (dog with microchip)
echo "[4/7] Creating animal (Biscuit the Lab)..."
ANIMAL=$(curl -s -X POST "$BASE/Animal" \
  -H "Content-Type: application/json" \
  -d "{\"resourceType\":\"Animal\",\"name\":\"Biscuit\",\"species\":\"canis-familiaris\",\"breed\":\"Labrador Retriever\",\"sex\":\"male\",\"neuterStatus\":\"neutered\",\"birthDate\":\"2019-03-15\",\"weightKg\":32.5,\"identifiers\":[{\"type\":\"microchip-iso\",\"value\":\"956000004287442\"}],\"owners\":[{\"ref\":\"Owner/$OWNER_ID\",\"role\":\"primary\"}]}")
ANIMAL_ID=$(echo "$ANIMAL" | jq -r '.id')
echo "    Animal: $ANIMAL_ID (chip: 956000004287442)"

# 5. Create encounter (GP visit)
echo "[5/7] Creating encounter..."
ENC=$(curl -s -X POST "$BASE/Encounter" \
  -H "Content-Type: application/json" \
  -d "{\"resourceType\":\"Encounter\",\"status\":\"completed\",\"class\":\"outpatient\",\"subject\":{\"ref\":\"Animal/$ANIMAL_ID\"},\"owner\":{\"ref\":\"Owner/$OWNER_ID\"},\"practitioners\":[{\"practitioner\":{\"ref\":\"Practitioner/$VET_ID\"},\"role\":\"attending\"}],\"period\":{\"start\":\"2026-05-16T14:00:00Z\",\"end\":\"2026-05-16T15:00:00Z\"},\"reasonText\":\"Annual wellness exam\"}")
ENC_ID=$(echo "$ENC" | jq -r '.id')
echo "    Encounter: $ENC_ID"

# 6. Record vitals
echo "[6/7] Recording vitals (vital signs panel)..."
OBS=$(curl -s -X POST "$BASE/Observation" \
  -H "Content-Type: application/json" \
  -d "{\"resourceType\":\"Observation\",\"status\":\"final\",\"category\":[\"vital-signs\"],\"code\":{\"code\":\"vitals-panel\",\"display\":\"Vital signs panel\"},\"subject\":{\"ref\":\"Animal/$ANIMAL_ID\"},\"encounter\":{\"ref\":\"Encounter/$ENC_ID\"},\"effectiveDateTime\":\"2026-05-16T14:10:00Z\",\"component\":[{\"code\":{\"code\":\"body-weight\"},\"valueQuantity\":{\"value\":32.5,\"unit\":\"kg\"}},{\"code\":{\"code\":\"temperature\"},\"valueQuantity\":{\"value\":38.6,\"unit\":\"C\"}},{\"code\":{\"code\":\"heart-rate\"},\"valueQuantity\":{\"value\":88,\"unit\":\"/min\"}}],\"interpretation\":\"normal\"}")
OBS_ID=$(echo "$OBS" | jq -r '.id')
echo "    Observation: $OBS_ID"

# 7. Search — retrieve everything for this animal
echo "[7/7] Searching all records for animal..."
echo ""
echo "  Conditions:"
curl -s "$BASE/Condition?subject=Animal/$ANIMAL_ID" | jq -r '.total'
echo "  MedicationRequests:"
curl -s "$BASE/MedicationRequest?subject=Animal/$ANIMAL_ID" | jq -r '.total'
echo "  Observations:"
curl -s "$BASE/Observation?subject=Animal/$ANIMAL_ID" | jq -r '.total'
echo ""
echo "  Search by microchip: $(curl -s "$BASE/Animal?identifier=microchip-iso|956000004287442" | jq -r '.entry[0].resource.name')"
echo ""
echo "=== Done. Visit recorded in VHIR. ==="
