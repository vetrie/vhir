"""Lost pet / microchip lookup walkthrough — Python SDK equivalent of docs/walkthroughs/lost-pet.sh

Flow:
  1. Register animal with microchip identifier
  2. Simulate a microchip scanner lookup
  3. Cross-reference to find owner contact information
"""
from __future__ import annotations

import asyncio

from vhir_sdk import VhirClient, collect
from vhir_sdk.models import (
    AnimalCreate,
    Identifier,
    OwnerCreate,
    OwnerLink,
    OwnerName,
    Reference,
    Telecom,
)

BASE_URL = "http://localhost:8000"
CHIP_ID = "900123456789012"


async def main() -> None:
    async with VhirClient(BASE_URL) as client:
        await client.obtain_dev_token(subject="shelter-staff", role="shelter")

        # 1. Register owner with contact info
        owner = await client.create_owner(
            OwnerCreate(
                name=OwnerName(given="Jamie", family="Rivera"),
                telecom=[
                    Telecom(system="phone", value="+1-555-0199", use="mobile"),
                    Telecom(system="email", value="jamie.rivera@example.com"),
                ],
            )
        )
        owner_id = owner["id"]
        print(f"Owner registered: {owner_id}")

        # 2. Register microchipped animal
        animal = await client.create_animal(
            AnimalCreate(
                species="felis-catus",
                breed="domestic-shorthair",
                name="Shadow",
                sex="male",
                neuterStatus="neutered",
                birthDate="2021-07-04",
                color="black",
                identifiers=[
                    Identifier(
                        type="microchip-iso",
                        value=CHIP_ID,
                        system="http://vhir.dev/cs/microchip",
                    )
                ],
                owners=[OwnerLink(ref=f"Owner/{owner_id}", role="primary")],
            )
        )
        animal_id = animal["id"]
        print(f"Animal registered: {animal_id} (chip: {CHIP_ID})")

        # 3. Simulate shelter scanner lookup
        print(f"\nScanner found chip: {CHIP_ID}")
        lookup = await client.lookup_microchip(CHIP_ID)

        if lookup.found:
            print(f"  Matched local animal: {lookup.localAnimal}")

            # Fetch the full animal record
            matched_animal_id = (lookup.localAnimal or "").split("/")[-1]
            if matched_animal_id:
                matched = await client.read_animal(matched_animal_id)
                print(f"  Animal name: {matched.get('name', 'unknown')}")
                print(f"  Species: {matched.get('species')}")

                # Find owner contact via search
                owner_links: list[dict] = matched.get("owners", [])
                for link in owner_links:
                    owner_ref_id = link["ref"].split("/")[-1]
                    owner_record = await client.read_owner(owner_ref_id)
                    name = owner_record.get("name", {})
                    full_name = f"{name.get('given', '')} {name.get('family', '')}".strip()
                    print(f"\n  Owner: {full_name}")
                    for tc in owner_record.get("telecom", []):
                        print(f"    {tc['system']}: {tc['value']}")
        else:
            print("  No match found — checking external registries...")
            if lookup.registry:
                print(f"  Registry: {lookup.registry}")

        print("\nLost pet lookup complete.")


if __name__ == "__main__":
    asyncio.run(main())
