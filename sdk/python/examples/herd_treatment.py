"""Herd treatment walkthrough — Python SDK equivalent of docs/walkthroughs/herd-treatment.sh

Flow:
  1. Create organisation + practitioner
  2. Create herd Group with members
  3. Open a herd encounter
  4. Write a VFD prescription for the herd
  5. Record group medication administration with withdrawal periods
"""
from __future__ import annotations

import asyncio

from vhir_sdk import VhirClient
from vhir_sdk.models import (
    AnimalCreate,
    Coding,
    DosageInstruction,
    DoseQuantity,
    EncounterCreate,
    GroupCreate,
    GroupMember,
    MedicationAdministrationCreate,
    MedicationInfo,
    MedicationRequestCreate,
    MemberCompletion,
    OrganizationCreate,
    OwnerCreate,
    OwnerName,
    PractitionerCreate,
    PractitionerName,
    PractitionerRoleCreate,
    Reference,
    WithdrawalEnds,
    WithdrawalPeriod,
)

BASE_URL = "http://localhost:8000"


async def main() -> None:
    async with VhirClient(BASE_URL) as client:
        await client.obtain_dev_token(subject="dr-miller", role="veterinarian")

        # 1. Create farm organisation
        org = await client.create_organization(
            OrganizationCreate(name="Green Pastures Farm", type="farm")
        )
        org_id = org["id"]

        # 2. Create practitioner (accredited VFD vet)
        vet = await client.create_practitioner(
            PractitionerCreate(
                name=PractitionerName(family="Miller", given="Beth"),
                deaNumber="BM1234567",
            )
        )
        vet_id = vet["id"]

        await client.create_practitioner_role(
            PractitionerRoleCreate(
                practitioner=Reference(ref=f"Practitioner/{vet_id}"),
                organization=Reference(ref=f"Organization/{org_id}"),
                role="veterinarian",
                specialties=["large-animal", "food-safety"],
            )
        )

        # 3. Create owner (farm operator)
        owner = await client.create_owner(
            OwnerCreate(name=OwnerName(given="Tom", family="Hansen"))
        )
        owner_id = owner["id"]

        # 4. Create three cattle
        cattle_ids: list[str] = []
        for tag in ["TAG-001", "TAG-002", "TAG-003"]:
            animal = await client.create_animal(
                AnimalCreate(
                    species="bos-taurus",
                    breed="angus",
                    name=f"Steer {tag}",
                )
            )
            cattle_ids.append(animal["id"])
        print(f"Cattle: {cattle_ids}")

        # 5. Create herd group
        group = await client.create_group(
            GroupCreate(
                name="Pen 4 — Steer Cohort",
                type="animal",
                productionPurpose="beef",
                managingOrganization=Reference(ref=f"Organization/{org_id}"),
                members=[GroupMember(ref=f"Animal/{cid}") for cid in cattle_ids],
                quantity=len(cattle_ids),
            )
        )
        group_id = group["id"]
        print(f"Group: {group_id}")

        # 6. Herd encounter
        encounter = await client.create_encounter(
            EncounterCreate(
                status="in-progress",
                **{"class": "FLD"},
                subject=Reference(ref=f"Group/{group_id}"),
                serviceProvider=Reference(ref=f"Organization/{org_id}"),
            )
        )
        enc_id = encounter["id"]

        # 7. VFD prescription (Tulathromycin)
        rx = await client.create_medication_request(
            MedicationRequestCreate(
                status="active",
                intent="order",
                medication=MedicationInfo(
                    name="Tulathromycin",
                    code="TUL",
                    form="injectable",
                    brand="Draxxin",
                ),
                subject=Reference(ref=f"Group/{group_id}"),
                requester=Reference(ref=f"Practitioner/{vet_id}"),
                encounter=Reference(ref=f"Encounter/{enc_id}"),
                vfd=True,
                dosageInstruction=[
                    DosageInstruction(
                        text="2.5 mg/kg SQ single dose",
                        route="subcutaneous",
                        doseQuantity=DoseQuantity(value=2.5, unit="mg/kg"),
                    )
                ],
                withdrawal=WithdrawalPeriod(meatHours=552),
            )
        )
        print(f"VFD Prescription: {rx['id']}")

        # 8. Record group administration
        adm = await client.create_medication_administration(
            MedicationAdministrationCreate(
                status="completed",
                medication=MedicationInfo(name="Tulathromycin", code="TUL", form="injectable"),
                subject=Reference(ref=f"Group/{group_id}"),
                encounter=Reference(ref=f"Encounter/{enc_id}"),
                effectiveDateTime="2026-05-17T08:00:00Z",
                withdrawalEnds=WithdrawalEnds(meat="2026-06-09"),
                memberCompletion=[
                    MemberCompletion(animal=f"Animal/{cid}", status="completed")
                    for cid in cattle_ids
                ],
            )
        )
        print(f"Administration: {adm['id']}")

        print("Herd treatment complete.")


if __name__ == "__main__":
    asyncio.run(main())
