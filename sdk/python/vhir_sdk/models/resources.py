"""Pydantic v2 models generated from spec/openapi.yaml — all VHIR resource types."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared primitive types
# ---------------------------------------------------------------------------


class Reference(BaseModel):
    ref: str = Field(description="ResourceType/id (e.g. 'Animal/01ABC')")
    display: str | None = None


class Coding(BaseModel):
    code: str
    system: str | None = None
    display: str | None = None


class Identifier(BaseModel):
    type: str
    value: str
    system: str | None = None
    issuer: Reference | None = None


class Telecom(BaseModel):
    system: str
    value: str
    use: str | None = None
    preferred: bool | None = None


class Address(BaseModel):
    line: list[str] = Field(default_factory=list)
    city: str | None = None
    state: str | None = None
    postalCode: str | None = None
    country: str | None = None


class Period(BaseModel):
    start: str | None = None
    end: str | None = None


class Quantity(BaseModel):
    value: float
    unit: str
    system: str = "http://unitsofmeasure.org"
    code: str | None = None


class DoseQuantity(BaseModel):
    value: float
    unit: str


# ---------------------------------------------------------------------------
# Animal
# ---------------------------------------------------------------------------


class OwnerLink(BaseModel):
    ref: str
    role: str
    grantedAt: str | None = None


class AnimalCreate(BaseModel):
    resourceType: str = "Animal"
    species: str
    name: str | None = None
    breed: str | None = None
    sex: str | None = None
    neuterStatus: str | None = None
    birthDate: str | None = None
    birthDateEstimated: bool = False
    deathDate: str | None = None
    deceased: bool = False
    color: str | None = None
    markings: str | None = None
    weightKg: float | None = None
    identifiers: list[Identifier] = Field(default_factory=list)
    owners: list[OwnerLink] = Field(default_factory=list)
    managingOrganization: Reference | None = None
    photo: str | None = None
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------


class OwnerName(BaseModel):
    given: str | None = None
    family: str | None = None
    full: str | None = None


class OwnerCreate(BaseModel):
    resourceType: str = "Owner"
    name: OwnerName | None = None
    ownerType: str = "individual"
    telecom: list[Telecom] = Field(default_factory=list)
    address: Address | None = None
    identifiers: list[Identifier] = Field(default_factory=list)
    preferredLanguage: str | None = None
    communicationPreferences: dict[str, Any] = Field(default_factory=dict)
    managingOrganization: Reference | None = None
    active: bool = True
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Practitioner
# ---------------------------------------------------------------------------


class PractitionerName(BaseModel):
    family: str
    given: str | None = None
    prefix: str | None = None
    suffix: str | None = None


class Qualification(BaseModel):
    code: str
    display: str | None = None
    licenseNumber: str | None = None
    jurisdiction: str | None = None
    issuer: Reference | None = None
    period: Period | None = None


class PractitionerCreate(BaseModel):
    resourceType: str = "Practitioner"
    name: PractitionerName | None = None
    telecom: list[Telecom] = Field(default_factory=list)
    qualifications: list[Qualification] = Field(default_factory=list)
    deaNumber: str | None = None
    npiNumber: str | None = None
    active: bool = True
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# PractitionerRole
# ---------------------------------------------------------------------------


class AvailableTime(BaseModel):
    daysOfWeek: list[str] = Field(default_factory=list)
    availableStartTime: str | None = None
    availableEndTime: str | None = None


class PractitionerRoleCreate(BaseModel):
    resourceType: str = "PractitionerRole"
    practitioner: Reference
    organization: Reference
    role: str
    specialties: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    denyPermissions: list[str] = Field(default_factory=list)
    period: Period | None = None
    availableTime: list[AvailableTime] = Field(default_factory=list)
    active: bool = True
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------


class OrganizationCreate(BaseModel):
    resourceType: str = "Organization"
    name: str
    type: str | None = None
    identifiers: list[Identifier] = Field(default_factory=list)
    telecom: list[Telecom] = Field(default_factory=list)
    address: Address | None = None
    timezone: str | None = None
    partOf: Reference | None = None
    active: bool = True
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Encounter
# ---------------------------------------------------------------------------


class EncounterPractitioner(BaseModel):
    practitioner: Reference
    role: str


class EncounterDiagnosis(BaseModel):
    condition: Reference
    use: str | None = None
    rank: int | None = None


class EncounterAdmission(BaseModel):
    origin: Reference | None = None
    admitSource: str | None = None
    dischargeDisposition: str | None = None


class EncounterCreate(BaseModel):
    resourceType: str = "Encounter"
    status: str
    # "class" is a reserved keyword; aliased field
    encounter_class: str = Field(alias="class")
    subject: Reference
    owner: Reference | None = None
    serviceProvider: Reference | None = None
    location: Reference | None = None
    practitioners: list[EncounterPractitioner] = Field(default_factory=list)
    period: Period | None = None
    reasonCode: list[Coding] = Field(default_factory=list)
    reasonText: str | None = None
    diagnosis: list[EncounterDiagnosis] = Field(default_factory=list)
    referredFrom: Reference | None = None
    admission: EncounterAdmission | None = None
    reportable: bool = False
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)


# ---------------------------------------------------------------------------
# Observation
# ---------------------------------------------------------------------------


class ObservationComponent(BaseModel):
    code: Coding
    valueQuantity: Quantity | None = None
    valueString: str | None = None
    valueCoding: Coding | None = None


class SampledData(BaseModel):
    origin: Quantity
    periodMs: float
    data: str
    factor: float = 1.0
    dimensions: int = 1


class ReferenceRange(BaseModel):
    low: float | None = None
    high: float | None = None
    unit: str | None = None
    text: str | None = None
    appliesTo: str | None = None


class ObservationCreate(BaseModel):
    resourceType: str = "Observation"
    status: str
    code: Coding
    subject: Reference
    category: list[str] = Field(default_factory=list)
    encounter: Reference | None = None
    device: Reference | None = None
    performer: list[Reference] = Field(default_factory=list)
    effectiveDateTime: str | None = None
    effectivePeriod: Period | None = None
    issued: str | None = None
    valueQuantity: Quantity | None = None
    valueString: str | None = None
    valueBoolean: bool | None = None
    valueInteger: int | None = None
    valueCoding: Coding | None = None
    component: list[ObservationComponent] = Field(default_factory=list)
    sampledData: SampledData | None = None
    referenceRange: list[ReferenceRange] = Field(default_factory=list)
    interpretation: str | None = None
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Condition
# ---------------------------------------------------------------------------


class ConditionEvidence(BaseModel):
    code: Coding | None = None
    detail: Reference | None = None


class ConditionCreate(BaseModel):
    resourceType: str = "Condition"
    status: str
    code: Coding
    subject: Reference
    verificationStatus: str | None = None
    encounter: Reference | None = None
    recorder: Reference | None = None
    asserter: Reference | None = None
    onsetDateTime: str | None = None
    onsetDate: str | None = None
    onsetString: str | None = None
    abatementDate: str | None = None
    recordedDate: str | None = None
    severity: str | None = None
    evidence: list[ConditionEvidence] = Field(default_factory=list)
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Immunization
# ---------------------------------------------------------------------------


class ImmunizationPerformer(BaseModel):
    practitioner: Reference
    role: str | None = None


class ImmunizationCreate(BaseModel):
    resourceType: str = "Immunization"
    status: str
    vaccineCode: Coding
    subject: Reference
    encounter: Reference | None = None
    occurrenceDateTime: str | None = None
    primarySource: bool = True
    site: str | None = None
    route: str | None = None
    doseQuantity: Quantity | None = None
    performer: list[ImmunizationPerformer] = Field(default_factory=list)
    lotNumber: str | None = None
    expirationDate: str | None = None
    nextDueDate: str | None = None
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# MedicationRequest
# ---------------------------------------------------------------------------


class MedicationInfo(BaseModel):
    name: str | None = None
    code: str | None = None
    system: str | None = None
    form: str | None = None
    brand: str | None = None


class DosageInstruction(BaseModel):
    text: str | None = None
    route: str | None = None
    doseQuantity: DoseQuantity | None = None
    frequency: str | None = None
    duration: str | None = None
    maxDosePerDay: DoseQuantity | None = None


class DispenseRequest(BaseModel):
    quantity: DoseQuantity | None = None
    numberOfRefillsAllowed: int | None = None
    externalPharmacy: bool = False


class ControlledSubstance(BaseModel):
    schedule: str | None = None
    deaOrderFormNumber: str | None = None


class WithdrawalPeriod(BaseModel):
    milkHours: float | None = None
    meatHours: float | None = None
    eggsHours: float | None = None
    notes: str | None = None


class MedicationRequestCreate(BaseModel):
    resourceType: str = "MedicationRequest"
    status: str
    intent: str
    medication: MedicationInfo
    subject: Reference
    requester: Reference
    encounter: Reference | None = None
    dispenser: Reference | None = None
    dosageInstruction: list[DosageInstruction] = Field(default_factory=list)
    dispenseRequest: DispenseRequest | None = None
    controlled: ControlledSubstance | None = None
    vfd: bool = False
    withdrawal: WithdrawalPeriod | None = None
    extraLabel: bool = False
    authoredOn: str | None = None
    expiresOn: str | None = None
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# MedicationDispense
# ---------------------------------------------------------------------------


class MedicationDispenseCreate(BaseModel):
    resourceType: str = "MedicationDispense"
    status: str
    medication: MedicationInfo
    subject: Reference
    authorizingPrescription: Reference | None = None
    quantity: DoseQuantity | None = None
    daysSupply: int | None = None
    whenPrepared: str | None = None
    whenHandedOver: str | None = None
    performer: Reference | None = None
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# MedicationAdministration
# ---------------------------------------------------------------------------


class WithdrawalEnds(BaseModel):
    meat: str | None = None
    milk: str | None = None
    eggs: str | None = None


class MemberCompletion(BaseModel):
    animal: str
    status: str
    effectiveDateTime: str | None = None
    note: str | None = None


class MedicationAdministrationCreate(BaseModel):
    resourceType: str = "MedicationAdministration"
    status: str
    medication: MedicationInfo
    subject: Reference
    encounter: Reference | None = None
    performer: list[Reference] = Field(default_factory=list)
    effectiveDateTime: str | None = None
    effectivePeriod: Period | None = None
    dosage: DosageInstruction | None = None
    withdrawalEnds: WithdrawalEnds | None = None
    memberCompletion: list[MemberCompletion] = Field(default_factory=list)
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Device
# ---------------------------------------------------------------------------


class DeviceCreate(BaseModel):
    resourceType: str = "Device"
    type: str
    status: str = "active"
    identifiers: list[Identifier] = Field(default_factory=list)
    subject: Reference | None = None
    owner: Reference | None = None
    manufacturer: str | None = None
    model: str | None = None
    serialNumber: str | None = None
    lotNumber: str | None = None
    manufactureDate: str | None = None
    expirationDate: str | None = None
    udi: str | None = None
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# DeviceMetric
# ---------------------------------------------------------------------------


class DeviceMetricCreate(BaseModel):
    resourceType: str = "DeviceMetric"
    device: Reference
    type: Coding
    category: str
    unit: Coding | None = None
    operationalStatus: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Group
# ---------------------------------------------------------------------------


class GroupMember(BaseModel):
    ref: str
    inactive: bool = False
    period: Period | None = None


class GroupCreate(BaseModel):
    resourceType: str = "Group"
    type: str = "animal"
    name: str | None = None
    productionPurpose: str | None = None
    premisesId: str | None = None
    managingOrganization: Reference | None = None
    active: bool = True
    quantity: int | None = None
    members: list[GroupMember] = Field(default_factory=list)
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# InsuranceClaim
# ---------------------------------------------------------------------------


class ClaimDiagnosis(BaseModel):
    condition: Reference
    sequence: int = 1


class ClaimProcedure(BaseModel):
    procedure: Reference
    sequence: int = 1


class ClaimItem(BaseModel):
    sequence: int
    serviceDate: str | None = None
    code: Coding | None = None
    quantity: Quantity | None = None
    unitPrice: float | None = None
    net: float | None = None


class PreAuthorization(BaseModel):
    requestedAt: str | None = None
    estimatedAmount: float | None = None
    currency: str = "USD"
    status: str | None = None
    authNumber: str | None = None
    respondedAt: str | None = None
    approvedAmount: float | None = None
    expiresAt: str | None = None
    notes: str | None = None


class ClaimSubmission(BaseModel):
    submittedAt: str | None = None
    claimedAmount: float | None = None
    currency: str = "USD"
    invoiceNumber: str | None = None
    paymentType: str | None = None


class ClaimAdjudication(BaseModel):
    adjudicatedAt: str | None = None
    outcome: str | None = None
    approvedAmount: float | None = None
    currency: str = "USD"
    deductibleApplied: float | None = None
    coinsuranceApplied: float | None = None
    paidAmount: float | None = None
    denialReason: str | None = None
    eobNumber: str | None = None
    notes: str | None = None


class InsuranceClaimCreate(BaseModel):
    resourceType: str = "InsuranceClaim"
    status: str
    subject: Reference
    type: str = "professional"
    encounter: Reference | None = None
    insurer: Reference | None = None
    policyNumber: str | None = None
    groupNumber: str | None = None
    claimType: str | None = None
    priority: str = "normal"
    diagnosis: list[ClaimDiagnosis] = Field(default_factory=list)
    procedure: list[ClaimProcedure] = Field(default_factory=list)
    item: list[ClaimItem] = Field(default_factory=list)
    totalAmount: float | None = None
    currency: str = "USD"
    preAuth: PreAuthorization | None = None
    submission: ClaimSubmission | None = None
    adjudication: ClaimAdjudication | None = None
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Appointment
# ---------------------------------------------------------------------------


class AppointmentParticipant(BaseModel):
    actor: Reference
    role: str | None = None
    status: str = "accepted"


class AppointmentCreate(BaseModel):
    resourceType: str = "Appointment"
    status: str
    subject: Reference
    serviceType: list[Coding] = Field(default_factory=list)
    practitioners: list[AppointmentParticipant] = Field(default_factory=list)
    start: str | None = None
    end: str | None = None
    slot: Reference | None = None
    comment: str | None = None
    priority: int = 0
    cancelationReason: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------


class ScheduleCreate(BaseModel):
    resourceType: str = "Schedule"
    actor: list[Reference] = Field(default_factory=list)
    planningHorizon: Period | None = None
    active: bool = True
    comment: str | None = None
    serviceType: list[Coding] = Field(default_factory=list)
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Slot
# ---------------------------------------------------------------------------


class SlotCreate(BaseModel):
    resourceType: str = "Slot"
    schedule: Reference
    status: str
    start: str
    end: str
    serviceType: list[Coding] = Field(default_factory=list)
    comment: str | None = None
    overbooked: bool = False
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------


class LocationCreate(BaseModel):
    resourceType: str = "Location"
    name: str
    type: str | None = None
    mode: str = "instance"
    description: str | None = None
    address: Address | None = None
    managingOrganization: Reference | None = None
    partOf: Reference | None = None
    operationalStatus: str | None = None
    active: bool = True
    telecom: list[Telecom] = Field(default_factory=list)
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Procedure
# ---------------------------------------------------------------------------


class ProcedurePerformer(BaseModel):
    practitioner: Reference
    role: str | None = None


class ProcedureCreate(BaseModel):
    resourceType: str = "Procedure"
    status: str
    code: Coding
    subject: Reference
    encounter: Reference | None = None
    performer: list[ProcedurePerformer] = Field(default_factory=list)
    performedDateTime: str | None = None
    performedPeriod: Period | None = None
    bodySite: str | None = None
    outcome: str | None = None
    followUp: str | None = None
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Microchip lookup (system operation)
# ---------------------------------------------------------------------------


class MicrochipLookupRequest(BaseModel):
    chipId: str


class MicrochipLookupResponse(BaseModel):
    found: bool
    localAnimal: str | None = None
    registry: dict[str, Any] | None = None
    registryContact: dict[str, Any] | None = None
    lastUpdated: str | None = None
    broker: str | None = None
