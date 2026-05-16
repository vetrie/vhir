#!/usr/bin/env bash
# VHIR walkthrough: lost pet microchip lookup
# Demonstrates the $lookup-microchip operation with local registry search
# Requires: curl, jq, running VHIR server on localhost:8000
set -euo pipefail
BASE="http://localhost:8000/v1"

echo "=== VHIR Lost Pet / Microchip Lookup Walkthrough ==="
echo ""

# 1. Register an animal with a microchip
echo "[1/3] Registering animal with ISO microchip..."
OWNER=$(curl -s -X POST "$BASE/Owner" \
  -H "Content-Type: application/json" \
  -d '{"resourceType":"Owner","name":{"given":"Sarah","family":"Chen"},"telecom":[{"system":"phone","value":"+1-555-7777","use":"mobile"},{"system":"email","value":"sarah@example.com"}]}')
OWNER_ID=$(echo "$OWNER" | jq -r '.id')

ANIMAL=$(curl -s -X POST "$BASE/Animal" \
  -H "Content-Type: application/json" \
  -d "{\"resourceType\":\"Animal\",\"name\":\"Oliver\",\"species\":\"felis-catus\",\"breed\":\"Domestic Shorthair\",\"sex\":\"male\",\"neuterStatus\":\"neutered\",\"identifiers\":[{\"type\":\"microchip-iso\",\"value\":\"956000012345678\"}],\"owners\":[{\"ref\":\"Owner/$OWNER_ID\",\"role\":\"primary\"}]}")
ANIMAL_ID=$(echo "$ANIMAL" | jq -r '.id')
echo "    Animal: $ANIMAL_ID (Oliver)"
echo "    Owner: $OWNER_ID (Sarah Chen)"
echo "    Chip: 956000012345678 (ISO 11784 FDX-B)"

# 2. Register the microchip as a Device record
echo ""
echo "[2/3] Recording chip implant as Device..."
DEVICE=$(curl -s -X POST "$BASE/Device" \
  -H "Content-Type: application/json" \
  -d "{\"resourceType\":\"Device\",\"type\":\"microchip-iso\",\"status\":\"active\",\"identifiers\":[{\"type\":\"microchip-iso\",\"value\":\"956000012345678\"}],\"subject\":{\"ref\":\"Animal/$ANIMAL_ID\"},\"manufacturer\":\"HomeAgain\",\"udi\":\"956000012345678\"}")
DEVICE_ID=$(echo "$DEVICE" | jq -r '.id')
echo "    Device: $DEVICE_ID"

# 3. Simulate chip scan at shelter / vet clinic
echo ""
echo "[3/3] Shelter scans chip — calling \$lookup-microchip..."
echo ""
LOOKUP=$(curl -s -X POST "$BASE/\$lookup-microchip" \
  -H "Content-Type: application/json" \
  -d '{"chipId":"956000012345678"}')
echo "$LOOKUP" | jq '.'

if [ "$(echo "$LOOKUP" | jq -r '.found')" = "true" ]; then
  ANIMAL_REF=$(echo "$LOOKUP" | jq -r '.localAnimal')
  echo ""
  echo "  Found in local registry: $ANIMAL_REF"
  echo "  Fetching animal details..."
  ANIMAL_DETAILS=$(curl -s "$BASE/$ANIMAL_REF")
  echo "  Name: $(echo "$ANIMAL_DETAILS" | jq -r '.name')"
  echo "  Species: $(echo "$ANIMAL_DETAILS" | jq -r '.species')"
  OWNER_REF=$(echo "$ANIMAL_DETAILS" | jq -r '.owners[0].ref')
  echo "  Owner ref: $OWNER_REF"
fi

echo ""
echo "--- Unknown chip (not in local registry) ---"
curl -s -X POST "$BASE/\$lookup-microchip" \
  -H "Content-Type: application/json" \
  -d '{"chipId":"999000000000000"}' | jq '.'

echo ""
echo "=== Done. Microchip lookup demonstrated. ==="
