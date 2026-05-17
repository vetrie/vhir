"""ezyVet ↔ VHIR bidirectional field mappings."""
from vhir_adapter_ezyvet.mappings.animal import animal_to_vhir, vhir_to_animal
from vhir_adapter_ezyvet.mappings.appointment import appointment_to_vhir, slot_to_vhir
from vhir_adapter_ezyvet.mappings.encounter import encounter_to_vhir
from vhir_adapter_ezyvet.mappings.immunization import vaccination_to_vhir
from vhir_adapter_ezyvet.mappings.medication import (
    dispense_item_to_medication_dispense,
    prescription_to_medication_request,
)
from vhir_adapter_ezyvet.mappings.observation import clinical_note_to_vhir
from vhir_adapter_ezyvet.mappings.owner import contact_to_vhir, vhir_to_contact

__all__ = [
    "animal_to_vhir",
    "vhir_to_animal",
    "contact_to_vhir",
    "vhir_to_contact",
    "encounter_to_vhir",
    "clinical_note_to_vhir",
    "prescription_to_medication_request",
    "dispense_item_to_medication_dispense",
    "vaccination_to_vhir",
    "appointment_to_vhir",
    "slot_to_vhir",
]
