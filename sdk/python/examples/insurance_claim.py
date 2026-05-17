"""Insurance claim walkthrough — Python SDK equivalent of docs/walkthroughs/insurance-claim.sh

Flow:
  1. Look up existing animal + encounter
  2. Record condition + procedure
  3. Build and submit insurance claim
  4. Simulate adjudication update
"""
from __future__ import annotations

import asyncio

from vhir_sdk import VhirClient, collect
from vhir_sdk.models import (
    AnimalCreate,
    ClaimAdjudication,
    ClaimDiagnosis,
    ClaimItem,
    ClaimProcedure,
    ClaimSubmission,
    Coding,
    ConditionCreate,
    EncounterCreate,
    InsuranceClaimCreate,
    OrganizationCreate,
    OwnerCreate,
    OwnerLink,
    OwnerName,
    PractitionerCreate,
    PractitionerName,
    PreAuthorization,
    ProcedureCreate,
    ProcedurePerformer,
    Quantity,
    Reference,
)

BASE_URL = "http://localhost:8000"


async def main() -> None:
    async with VhirClient(BASE_URL) as client:
        await client.obtain_dev_token(subject="billing-staff", role="administrator")

        # Setup: owner, animal, insurer, practitioner, encounter
        owner = await client.create_owner(
            OwnerCreate(name=OwnerName(given="Marcus", family="Webb"))
        )
        animal = await client.create_animal(
            AnimalCreate(
                species="felis-catus",
                name="Luna",
                sex="female",
                neuterStatus="spayed",
                owners=[OwnerLink(ref=f"Owner/{owner['id']}", role="primary")],
            )
        )
        animal_id = animal["id"]

        insurer = await client.create_organization(
            OrganizationCreate(name="PetShield Insurance", type="insurance")
        )
        vet = await client.create_practitioner(
            PractitionerCreate(name=PractitionerName(family="Park", given="Kim"))
        )
        encounter = await client.create_encounter(
            EncounterCreate(
                status="finished",
                **{"class": "AMB"},
                subject=Reference(ref=f"Animal/{animal_id}"),
            )
        )
        enc_id = encounter["id"]

        # 1. Record diagnosis
        condition = await client.create_condition(
            ConditionCreate(
                status="active",
                code=Coding(
                    system="http://hl7.org/fhir/sid/icd-10-cm",
                    code="K29.70",
                    display="Gastritis, unspecified",
                ),
                subject=Reference(ref=f"Animal/{animal_id}"),
                encounter=Reference(ref=f"Encounter/{enc_id}"),
                recorder=Reference(ref=f"Practitioner/{vet['id']}"),
            )
        )
        cond_id = condition["id"]
        print(f"Condition: {cond_id}")

        # 2. Record procedure
        procedure = await client.create_procedure(
            ProcedureCreate(
                status="completed",
                code=Coding(
                    system="http://www.ama-assn.org/go/cpt",
                    code="90784",
                    display="Therapeutic injection",
                ),
                subject=Reference(ref=f"Animal/{animal_id}"),
                encounter=Reference(ref=f"Encounter/{enc_id}"),
                performer=[ProcedurePerformer(practitioner=Reference(ref=f"Practitioner/{vet['id']}"))],
                performedDateTime="2026-05-17T11:00:00Z",
            )
        )
        proc_id = procedure["id"]
        print(f"Procedure: {proc_id}")

        # 3. Build claim with pre-auth
        claim = await client.create_insurance_claim(
            InsuranceClaimCreate(
                status="active",
                subject=Reference(ref=f"Animal/{animal_id}"),
                encounter=Reference(ref=f"Encounter/{enc_id}"),
                insurer=Reference(ref=f"Organization/{insurer['id']}"),
                policyNumber="PS-2026-00123",
                priority="normal",
                diagnosis=[ClaimDiagnosis(condition=Reference(ref=f"Condition/{cond_id}"))],
                procedure=[ClaimProcedure(procedure=Reference(ref=f"Procedure/{proc_id}"))],
                item=[
                    ClaimItem(sequence=1, code=Coding(code="90784"), unitPrice=85.00, net=85.00),
                    ClaimItem(sequence=2, code=Coding(code="99213"), unitPrice=150.00, net=150.00),
                ],
                totalAmount=235.00,
                preAuth=PreAuthorization(status="approved", authNumber="AUTH-2026-789"),
                submission=ClaimSubmission(
                    submittedAt="2026-05-17T14:00:00Z",
                    claimedAmount=235.00,
                    invoiceNumber="INV-0042",
                ),
            )
        )
        claim_id = claim["id"]
        print(f"Claim submitted: {claim_id}")

        # 4. Simulate adjudication (insurer response)
        adjudicated = await client.update_insurance_claim(
            claim_id,
            InsuranceClaimCreate(
                status="completed",
                subject=Reference(ref=f"Animal/{animal_id}"),
                adjudication=ClaimAdjudication(
                    outcome="approved",
                    approvedAmount=200.00,
                    deductibleApplied=35.00,
                    paidAmount=200.00,
                    eobNumber="EOB-2026-001",
                ),
            ),
        )
        print(f"Adjudication outcome: {adjudicated.get('adjudication', {}).get('outcome')}")
        print("Insurance claim flow complete.")


if __name__ == "__main__":
    asyncio.run(main())
