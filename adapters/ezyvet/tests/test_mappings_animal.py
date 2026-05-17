"""Unit tests for Animal mapping functions."""
from vhir_adapter_ezyvet.mappings.animal import animal_to_vhir, vhir_to_animal


def _ez_animal(**field_overrides):
    return {
        "id": "101",
        "active": 1,
        "fields": {
            "name": "Buddy",
            "species": {"id": "1", "name": "Canine"},
            "breed": {"id": "5", "name": "Labrador"},
            "sex": {"id": "1", "name": "Male Entire"},
            "date_of_birth": "2018-06-15",
            "is_deceased": 0,
            "color": "Yellow",
            "weight": "28.5",
            "microchip": "9876543210",
            "contact_id": "456",
            **field_overrides,
        },
    }


def test_animal_to_vhir_basic_fields():
    result = animal_to_vhir(_ez_animal())
    assert result["resourceType"] == "Animal"
    assert result["name"] == "Buddy"
    assert result["species"] == "canine"
    assert result["breed"] == "Labrador"
    assert result["sex"] == "male"
    assert result["birthDate"] == "2018-06-15"
    assert result["deceased"] is False
    assert result["weightKg"] == 28.5
    assert result["color"] == "Yellow"


def test_animal_to_vhir_identifiers():
    result = animal_to_vhir(_ez_animal())
    types = {i["type"] for i in result["identifiers"]}
    assert "ezyvet-id" in types
    assert "microchip" in types


def test_animal_to_vhir_owner_link():
    result = animal_to_vhir(_ez_animal())
    assert any(o["ref"] == "Owner/456" for o in result["owners"])


def test_animal_to_vhir_deceased():
    result = animal_to_vhir(_ez_animal(is_deceased=1, date_of_death="2023-01-10"))
    assert result["deceased"] is True
    assert result["deathDate"] == "2023-01-10"


def test_animal_to_vhir_unknown_species():
    result = animal_to_vhir(_ez_animal(**{"species": {"id": "99", "name": "Alien"}}))
    assert result["species"] == "other"


def test_animal_to_vhir_spayed_female():
    result = animal_to_vhir(_ez_animal(**{"sex": {"id": "4", "name": "Female Spayed"}}))
    assert result["sex"] == "spayed-female"


def test_animal_to_vhir_unix_timestamp_birthdate():
    result = animal_to_vhir(_ez_animal(date_of_birth="0"))
    assert result["birthDate"] is None


def test_vhir_to_animal_roundtrip():
    vhir = {
        "name": "Max",
        "species": "feline",
        "sex": "spayed-female",
        "birthDate": "2020-03-01",
        "breed": "Siamese",
        "color": "White",
        "weightKg": 4.2,
    }
    payload = vhir_to_animal(vhir)
    assert payload["fields"]["name"] == "Max"
    assert payload["fields"]["species"] == "Feline"
    assert payload["fields"]["sex"] == "Female Spayed"
    assert payload["fields"]["date_of_birth"] == "2020-03-01"
    assert payload["fields"]["weight"] == "4.2"


def test_vhir_to_animal_partial():
    payload = vhir_to_animal({"name": "Rex"})
    assert payload["fields"]["name"] == "Rex"
    assert "sex" not in payload["fields"]
