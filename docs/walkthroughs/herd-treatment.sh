#!/usr/bin/env bash
# VHIR walkthrough: food-animal herd treatment with withdrawal tracking
# Requires: curl, jq, running VHIR server on localhost:8000
set -euo pipefail
BASE="http://localhost:8000/v1"

echo "=== VHIR Herd Treatment Walkthrough ==="
echo ""

# 1. Create farm organization
echo "[1/6] Creating farm..."
FARM=$(curl -s -X POST "$BASE/Organization" \
  -H "Content-Type: application/json" \
  -d '{"resourceType":"Organization","name":"Rolling Hills Dairy","type":"farm"}')
FARM_ID=$(echo "$FARM" | jq -r '.id')
echo "    Organization: $FARM_ID"

# 2. Create veterinarian
echo "[2/6] Creating food-animal veterinarian..."
VET=$(curl -s -X POST "$BASE/Practitioner" \
  -H "Content-Type: application/json" \
  -d '{"resourceType":"Practitioner","name":{"given":"James","family":"Rivera","suffix":"DVM"},"qualifications":[{"code":"DVM","licenseNumber":"WI-DVM-11111"}]}')
VET_ID=$(echo "$VET" | jq -r '.id')
echo "    Practitioner: $VET_ID"

# 3. Create three cattle (USDA 840 EIDs)
echo "[3/6] Creating cattle..."
COW1=$(curl -s -X POST "$BASE/Animal" \
  -H "Content-Type: application/json" \
  -d '{"resourceType":"Animal","species":"bos-taurus","identifiers":[{"type":"usda-840","value":"840000012340001"}]}')
COW1_ID=$(echo "$COW1" | jq -r '.id')

COW2=$(curl -s -X POST "$BASE/Animal" \
  -H "Content-Type: application/json" \
  -d '{"resourceType":"Animal","species":"bos-taurus","identifiers":[{"type":"usda-840","value":"840000012340002"}]}')
COW2_ID=$(echo "$COW2" | jq -r '.id')

COW3=$(curl -s -X POST "$BASE/Animal" \
  -H "Content-Type: application/json" \
  -d '{"resourceType":"Animal","species":"bos-taurus","identifiers":[{"type":"usda-840","value":"840000012340003"}]}')
COW3_ID=$(echo "$COW3" | jq -r '.id')
echo "    Animals: $COW1_ID, $COW2_ID, $COW3_ID"

# 4. Create herd group
echo "[4/6] Creating herd group..."
GROUP=$(curl -s -X POST "$BASE/Group" \
  -H "Content-Type: application/json" \
  -d "{\"resourceType\":\"Group\",\"name\":\"Pen 4\",\"type\":\"animal\",\"productionPurpose\":\"dairy\",\"premisesId\":\"US-PIN-WI-88888\",\"managingOrganization\":{\"ref\":\"Organization/$FARM_ID\"},\"members\":[{\"ref\":\"Animal/$COW1_ID\"},{\"ref\":\"Animal/$COW2_ID\"},{\"ref\":\"Animal/$COW3_ID\"}]}")
GROUP_ID=$(echo "$GROUP" | jq -r '.id')
echo "    Group: $GROUP_ID (3 animals)"

# 5. Prescribe treatment
echo "[5/6] Prescribing pirlimycin for mastitis..."
RX=$(curl -s -X POST "$BASE/MedicationRequest" \
  -H "Content-Type: application/json" \
  -d "{\"resourceType\":\"MedicationRequest\",\"status\":\"active\",\"intent\":\"order\",\"medication\":{\"name\":\"Pirlimycin HCl 50mg/mL\",\"form\":\"intramammary infusion\"},\"subject\":{\"ref\":\"Group/$GROUP_ID\"},\"requester\":{\"ref\":\"Practitioner/$VET_ID\"},\"withdrawal\":{\"milkHours\":36,\"meatHours\":720},\"dosageInstruction\":[{\"route\":\"intramammary\",\"text\":\"1 tube per affected quarter, once daily x 2d\"}]}")
RX_ID=$(echo "$RX" | jq -r '.id')
echo "    MedicationRequest: $RX_ID"
echo "    Withdrawal: milk=$(echo $RX | jq '.withdrawal.milkHours')h, meat=$(echo $RX | jq '.withdrawal.meatHours')h"

# 6. Record administration with per-member completion
echo "[6/6] Recording administration with per-animal completion..."
ADMIN=$(curl -s -X POST "$BASE/MedicationAdministration" \
  -H "Content-Type: application/json" \
  -d "{\"resourceType\":\"MedicationAdministration\",\"status\":\"completed\",\"medication\":{\"name\":\"Pirlimycin HCl 50mg/mL\",\"form\":\"intramammary infusion\"},\"subject\":{\"ref\":\"Group/$GROUP_ID\"},\"performer\":[{\"ref\":\"Practitioner/$VET_ID\"}],\"effectiveDateTime\":\"2026-05-17T07:00:00Z\",\"withdrawalEnds\":{\"milk\":\"2026-05-18\",\"meat\":\"2026-07-16\"},\"memberCompletion\":[{\"animal\":\"Animal/$COW1_ID\",\"status\":\"completed\",\"effectiveDateTime\":\"2026-05-17T07:01:00Z\"},{\"animal\":\"Animal/$COW2_ID\",\"status\":\"completed\",\"effectiveDateTime\":\"2026-05-17T07:05:00Z\"},{\"animal\":\"Animal/$COW3_ID\",\"status\":\"refused\"}]}")
ADMIN_ID=$(echo "$ADMIN" | jq -r '.id')
echo "    MedicationAdministration: $ADMIN_ID"
echo "    Member completions:"
echo "$ADMIN" | jq -r '.memberCompletion[] | "      \(.animal): \(.status)"'

echo ""
echo "  Records for herd:"
echo "  MedicationRequests: $(curl -s "$BASE/MedicationRequest?subject=Group/$GROUP_ID" | jq -r '.total')"
echo "  MedicationAdministrations: $(curl -s "$BASE/MedicationAdministration?subject=Group/$GROUP_ID" | jq -r '.total')"
echo ""
echo "=== Done. Withdrawal period ends milk:$(echo $ADMIN | jq -r '.withdrawalEnds.milk') meat:$(echo $ADMIN | jq -r '.withdrawalEnds.meat') ==="
