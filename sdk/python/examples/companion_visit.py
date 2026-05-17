"""Companion animal visit walkthrough — Python SDK equivalent of docs/walkthroughs/companion-visit.sh

Flow:
  1. Obtain dev token
  2. Register owner + animal
  3. Open encounter
  4. Record weight observation
  5. Record rabies immunization
  6. Write prescription
  7. Dispense & administer medication
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
    ImmunizationCreate,
    ImmunizationPerformer,
    MedicationAdministrationCreate,
    MedicationDispenseCreate,
    MedicationInfo,
    MedicationRequestCreate,
    ObservationCreate,
    OwnerCreate,
    OwnerLink,
    OwnerName,
    PractitionerCreate,
    PractitionerName,
    Quantity,
    Reference,
    Telecom,
)

BASE_URL = "http://localhost:8000"


async def main() -> None:
    async with VhirClient(BASE_URL) as client:
        token = await client.obtain_dev_token(subject="dr-jones", role="veterinarian")
        print(f"Token: {token[:20]}...")

        # 1. Register owner
        owner = await client.create_owner(
            OwnerCreate(
                name=OwnerName(given="Sarah", family="Chen"),
                telecom=[Telecom(system="phone", value="+1-555-0100")],
            )
        )
        owner_id = owner["id"]
        print(f"Owner: {owner_id}")

        # 2. Register the practitioner
        vet = await client.create_practitioner(
            PractitionerCreate(name=PractitionerName(family="Jones", given="Alex"))
        )
        vet_id = vet["id"]

        # 3. Register the animal
        animal = await client.create_animal(
            AnimalCreate(
                species="canis-familiaris",
                breed="labrador-retriever",
                name="Buddy",
                sex="male",
                neuterStatus="neutered",
                birthDate="2020-03-15",
                owners=[OwnerLink(ref=f"Owner/{owner_id}", role="primary")],
            )
        )
        animal_id = animal["id"]
        print(f"Animal: {animal_id}")

        # 4. Open encounter
        encounter = await client.create_encounter(
            EncounterCreate(
                status="in-progress",
                **{"class": "AMB"},
                subject=Reference(ref=f"Animal/{animal_id}"),
                owner=Reference(ref=f"Owner/{owner_id}"),
            )
        )
        enc_id = encounter["id"]
        print(f"Encounter: {enc_id}")

        # 5. Record weight
        obs = await client.create_observation(
            ObservationCreate(
                status="final",
                code=Coding(
                    system="http://loinc.org",
                    code="29463-7",
                    display="Body weight",
                ),
                subject=Reference(ref=f"Animal/{animal_id}"),
                encounter=Reference(ref=f"Encounter/{enc_id}"),
                valueQuantity=Quantity(value=28.5, unit="kg"),
            )
        )
        print(f"Observation (weight): {obs['id']}")

        # 6. Record rabies immunization
        imm = await client.create_immunization(
            ImmunizationCreate(
                status="completed",
                vaccineCode=Coding(
                    system="http://vhir.dev/cs/vaccine-codes",
                    code="rabies-1yr",
                    display="Rabies 1-year",
                ),
                subject=Reference(ref=f"Animal/{animal_id}"),
                encounter=Reference(ref=f"Encounter/{enc_id}"),
                performer=[ImmunizationPerformer(practitioner=Reference(ref=f"Practitioner/{vet_id}"))],
                occurrenceDateTime="2026-05-17T10:30:00Z",
                nextDueDate="2027-05-17",
            )
        )
        print(f"Immunization (rabies): {imm['id']}")

        # 7. Prescribe amoxicillin
        rx = await client.create_medication_request(
            MedicationRequestCreate(
                status="active",
                intent="order",
                medication=MedicationInfo(name="Amoxicillin", code="AMX250", form="capsule"),
                subject=Reference(ref=f"Animal/{animal_id}"),
                requester=Reference(ref=f"Practitioner/{vet_id}"),
                encounter=Reference(ref=f"Encounter/{enc_id}"),
                dosageInstruction=[
                    DosageInstruction(
                        text="1 capsule twice daily with food",
                        route="oral",
                        doseQuantity=DoseQuantity(value=250, unit="mg"),
                        frequency="BID",
                        duration="10 days",
                    )
                ],
            )
        )
        print(f"Prescription: {rx['id']}")

        # 8. Dispense
        dispense = await client.create_medication_dispense(
            MedicationDispenseCreate(
                status="completed",
                medication=MedicationInfo(name="Amoxicillin", code="AMX250", form="capsule"),
                subject=Reference(ref=f"Animal/{animal_id}"),
                authorizingPrescription=Reference(ref=f"MedicationRequest/{rx['id']}"),
                daysSupply=10,
            )
        )
        print(f"Dispense: {dispense['id']}")

        # 9. Close encounter
        await client.update_encounter(
            enc_id,
            EncounterCreate(
                status="finished",
                **{"class": "AMB"},
                subject=Reference(ref=f"Animal/{animal_id}"),
            ),
        )
        print("Encounter closed — companion visit complete.")


if __name__ == "__main__":
    asyncio.run(main())
