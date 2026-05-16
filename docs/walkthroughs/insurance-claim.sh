#!/usr/bin/env bash
# VHIR walkthrough: pet insurance claim — Trupanion VetDirectPay pre-auth + adjudication
# Requires: curl, jq, running VHIR server on localhost:8000
set -euo pipefail
BASE="http://localhost:8000/v1"

echo "=== VHIR Pet Insurance Claim Walkthrough ==="
echo ""

# 1. Create insurer
echo "[1/7] Creating insurer (Trupanion)..."
INSURER=$(curl -s -X POST "$BASE/Organization" \
  -H "Content-Type: application/json" \
  -d '{"resourceType":"Organization","name":"Trupanion","type":"insurer","telecom":[{"system":"phone","value":"+1-800-908-4738"}]}')
INSURER_ID=$(echo "$INSURER" | jq -r '.id')
echo "    Organization: $INSURER_ID"

# 2. Create clinic
echo "[2/7] Creating clinic..."
CLINIC=$(curl -s -X POST "$BASE/Organization" \
  -H "Content-Type: application/json" \
  -d '{"resourceType":"Organization","name":"Blue Cross Animal Hospital","type":"clinic"}')
CLINIC_ID=$(echo "$CLINIC" | jq -r '.id')
echo "    Organization: $CLINIC_ID"

# 3. Create patient (animal)
echo "[3/7] Creating patient..."
OWNER=$(curl -s -X POST "$BASE/Owner" \
  -H "Content-Type: application/json" \
  -d '{"resourceType":"Owner","name":{"given":"Maya","family":"Patel"},"telecom":[{"system":"email","value":"maya@example.com"}]}')
OWNER_ID=$(echo "$OWNER" | jq -r '.id')

ANIMAL=$(curl -s -X POST "$BASE/Animal" \
  -H "Content-Type: application/json" \
  -d "{\"resourceType\":\"Animal\",\"name\":\"Bruno\",\"species\":\"canis-familiaris\",\"breed\":\"German Shepherd\",\"sex\":\"male\",\"neuterStatus\":\"neutered\",\"identifiers\":[{\"type\":\"microchip-iso\",\"value\":\"956000099988877\"}],\"owners\":[{\"ref\":\"Owner/$OWNER_ID\",\"role\":\"primary\"}]}")
ANIMAL_ID=$(echo "$ANIMAL" | jq -r '.id')
echo "    Animal: $ANIMAL_ID (Bruno)"

# 4. Create encounter (TPLO surgery)
echo "[4/7] Creating encounter (TPLO surgery)..."
VET=$(curl -s -X POST "$BASE/Practitioner" \
  -H "Content-Type: application/json" \
  -d '{"resourceType":"Practitioner","name":{"given":"David","family":"Okonkwo","suffix":"DVM, DACVS"},"qualifications":[{"code":"DACVS","licenseNumber":"CA-DVM-77777"}]}')
VET_ID=$(echo "$VET" | jq -r '.id')

ENC=$(curl -s -X POST "$BASE/Encounter" \
  -H "Content-Type: application/json" \
  -d "{\"resourceType\":\"Encounter\",\"status\":\"planned\",\"class\":\"inpatient\",\"subject\":{\"ref\":\"Animal/$ANIMAL_ID\"},\"practitioners\":[{\"practitioner\":{\"ref\":\"Practitioner/$VET_ID\"},\"role\":\"surgeon\"}],\"reasonText\":\"Cranial cruciate ligament rupture — TPLO surgery\",\"serviceProvider\":{\"ref\":\"Organization/$CLINIC_ID\"}}")
ENC_ID=$(echo "$ENC" | jq -r '.id')
echo "    Encounter: $ENC_ID"

# 5. Pre-authorization request (VetDirectPay)
echo "[5/7] Submitting pre-authorization to Trupanion..."
CLAIM=$(curl -s -X POST "$BASE/InsuranceClaim" \
  -H "Content-Type: application/json" \
  -d "{\"resourceType\":\"InsuranceClaim\",\"status\":\"active\",\"type\":\"professional\",\"subject\":{\"ref\":\"Animal/$ANIMAL_ID\"},\"encounter\":{\"ref\":\"Encounter/$ENC_ID\"},\"insurer\":{\"ref\":\"Organization/$INSURER_ID\"},\"policyNumber\":\"TRU-8827364\",\"claimType\":\"pre-auth\",\"item\":[{\"sequence\":1,\"code\":{\"code\":\"surgery\",\"display\":\"TPLO — tibial plateau leveling osteotomy\"},\"net\":4200.00},{\"sequence\":2,\"code\":{\"code\":\"anesthesia\",\"display\":\"General anesthesia\"},\"net\":350.00},{\"sequence\":3,\"code\":{\"code\":\"hospitalization\",\"display\":\"Overnight hospitalization\"},\"net\":250.00}],\"totalAmount\":4800.00,\"currency\":\"USD\",\"preAuth\":{\"requestedAt\":\"2026-05-17T09:00:00Z\",\"estimatedAmount\":4800.00,\"currency\":\"USD\",\"status\":\"pending\"}}")
CLAIM_ID=$(echo "$CLAIM" | jq -r '.id')
echo "    InsuranceClaim: $CLAIM_ID"
echo "    Status: $(echo "$CLAIM" | jq -r '.preAuth.status')"
echo "    Estimated: \$$(echo "$CLAIM" | jq -r '.preAuth.estimatedAmount')"

# 6. Simulate insurer approval (update with auth number + approved amount)
echo ""
echo "[6/7] Trupanion responds — approved \$4,300 (auth #AUTH-20260517-001)..."
CLAIM_BODY=$(curl -s "$BASE/InsuranceClaim/$CLAIM_ID")
# Patch in approval (using PUT with updated fields)
curl -s -X PUT "$BASE/InsuranceClaim/$CLAIM_ID" \
  -H "Content-Type: application/json" \
  -d "{\"resourceType\":\"InsuranceClaim\",\"status\":\"active\",\"type\":\"professional\",\"subject\":{\"ref\":\"Animal/$ANIMAL_ID\"},\"encounter\":{\"ref\":\"Encounter/$ENC_ID\"},\"insurer\":{\"ref\":\"Organization/$INSURER_ID\"},\"policyNumber\":\"TRU-8827364\",\"claimType\":\"pre-auth\",\"totalAmount\":4800.00,\"currency\":\"USD\",\"preAuth\":{\"requestedAt\":\"2026-05-17T09:00:00Z\",\"estimatedAmount\":4800.00,\"currency\":\"USD\",\"status\":\"approved\",\"authNumber\":\"AUTH-20260517-001\",\"respondedAt\":\"2026-05-17T10:30:00Z\",\"approvedAmount\":4300.00,\"expiresAt\":\"2026-06-17T00:00:00Z\"}}" \
  | jq '{id:.id, authNumber:.preAuth.authNumber, approvedAmount:.preAuth.approvedAmount}'

# 7. Post-service adjudication
echo ""
echo "[7/7] Post-surgery: submitting adjudication..."
curl -s -X PUT "$BASE/InsuranceClaim/$CLAIM_ID" \
  -H "Content-Type: application/json" \
  -d "{\"resourceType\":\"InsuranceClaim\",\"status\":\"completed\",\"type\":\"professional\",\"subject\":{\"ref\":\"Animal/$ANIMAL_ID\"},\"encounter\":{\"ref\":\"Encounter/$ENC_ID\"},\"insurer\":{\"ref\":\"Organization/$INSURER_ID\"},\"policyNumber\":\"TRU-8827364\",\"claimType\":\"pre-auth\",\"totalAmount\":4800.00,\"currency\":\"USD\",\"adjudication\":{\"adjudicatedAt\":\"2026-05-25T14:00:00Z\",\"outcome\":\"approved\",\"approvedAmount\":4300.00,\"deductibleApplied\":100.00,\"coinsuranceApplied\":0,\"paidAmount\":4200.00,\"eobNumber\":\"EOB-TRU-2026-009988\"}}" \
  | jq '{outcome:.adjudication.outcome, paidAmount:.adjudication.paidAmount, eob:.adjudication.eobNumber}'

echo ""
echo "=== Done. Insurance claim lifecycle complete. ==="
