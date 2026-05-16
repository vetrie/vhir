"""Pydantic models for all VHIR resources (M0 set)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


# ── Shared primitives ──────────────────────────────────────────────────────────

class Meta(BaseModel):
    version: int = 1
    lastUpdated: datetime | None = None
    profiles: list[str] = Field(default_factory=list)


class Reference(BaseModel):
    ref: str = Field(..., description="ResourceType/id")
    display: str | None = None


class Coding(BaseModel):
    system: str | None = None
    code: str
    display: str | None = None


class Identifier(BaseModel):
    type: str
    system: str | None = None
    value: str
    issuer: Reference | None = None


class Quantity(BaseModel):
    value: float
    unit: str
    system: str = "http://unitsofmeasure.org"
    code: str | None = None


class Period(BaseModel):
    start: date | datetime | None = None
    end: date | datetime | None = None


class Address(BaseModel):
    line: list[str] = Field(default_factory=list)
    city: str | None = None
    state: str | None = None
    postalCode: str | None = None
    country: str | None = None


class Telecom(BaseModel):
    system: str
    value: str
    use: str | None = None
    preferred: bool | None = None


# ── Bundle ─────────────────────────────────────────────────────────────────────

class BundleEntry(BaseModel):
    resource: dict[str, Any]
    search: dict[str, Any] | None = None


class Bundle(BaseModel):
    resourceType: Literal["Bundle"] = "Bundle"
    id: str | None = None
    type: str
    total: int | None = None
    link: list[dict[str, str]] = Field(default_factory=list)
    entry: list[BundleEntry] = Field(default_factory=list)


# ── Animal ─────────────────────────────────────────────────────────────────────

class OwnerLink(BaseModel):
    ref: str
    role: str
    grantedAt: datetime | None = None


class AnimalCreate(BaseModel):
    resourceType: Literal["Animal"] = "Animal"
    name: str | None = None
    species: str
    breed: str | None = None
    sex: str | None = None
    neuterStatus: str | None = None
    birthDate: date | None = None
    birthDateEstimated: bool = False
    deathDate: date | None = None
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


class Animal(AnimalCreate):
    id: str
    meta: Meta = Field(default_factory=Meta)


# ── Owner ──────────────────────────────────────────────────────────────────────

class OwnerName(BaseModel):
    given: str | None = None
    family: str | None = None
    full: str | None = None


class OwnerCreate(BaseModel):
    resourceType: Literal["Owner"] = "Owner"
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


class Owner(OwnerCreate):
    id: str
    meta: Meta = Field(default_factory=Meta)


# ── Practitioner ───────────────────────────────────────────────────────────────

class PractitionerName(BaseModel):
    given: str | None = None
    family: str
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
    resourceType: Literal["Practitioner"] = "Practitioner"
    name: PractitionerName | None = None
    telecom: list[Telecom] = Field(default_factory=list)
    qualifications: list[Qualification] = Field(default_factory=list)
    deaNumber: str | None = None
    npiNumber: str | None = None
    active: bool = True
    extensions: dict[str, Any] = Field(default_factory=dict)


class Practitioner(PractitionerCreate):
    id: str
    meta: Meta = Field(default_factory=Meta)


# ── PractitionerRole ───────────────────────────────────────────────────────────

class AvailableTime(BaseModel):
    daysOfWeek: list[str] = Field(default_factory=list)
    availableStartTime: str | None = None
    availableEndTime: str | None = None


class PractitionerRoleCreate(BaseModel):
    resourceType: Literal["PractitionerRole"] = "PractitionerRole"
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


class PractitionerRole(PractitionerRoleCreate):
    id: str
    meta: Meta = Field(default_factory=Meta)


# ── Organization ───────────────────────────────────────────────────────────────

class OrganizationCreate(BaseModel):
    resourceType: Literal["Organization"] = "Organization"
    name: str
    type: str | None = None
    identifiers: list[Identifier] = Field(default_factory=list)
    telecom: list[Telecom] = Field(default_factory=list)
    address: Address | None = None
    timezone: str | None = None
    partOf: Reference | None = None
    active: bool = True
    extensions: dict[str, Any] = Field(default_factory=dict)


class Organization(OrganizationCreate):
    id: str
    meta: Meta = Field(default_factory=Meta)


# ── Encounter ──────────────────────────────────────────────────────────────────

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
    resourceType: Literal["Encounter"] = "Encounter"
    status: str
    cls: str = Field(..., alias="class")
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


class Encounter(EncounterCreate):
    id: str
    meta: Meta = Field(default_factory=Meta)


# ── Observation ────────────────────────────────────────────────────────────────

class ObservationComponent(BaseModel):
    code: Coding
    valueQuantity: Quantity | None = None
    valueString: str | None = None
    valueCoding: Coding | None = None


class SampledData(BaseModel):
    origin: Quantity
    periodMs: float
    factor: float = 1.0
    dimensions: int = 1
    data: str


class ReferenceRange(BaseModel):
    low: float | None = None
    high: float | None = None
    unit: str | None = None
    text: str | None = None
    appliesTo: str | None = None


class ObservationCreate(BaseModel):
    resourceType: Literal["Observation"] = "Observation"
    status: str
    category: list[str] = Field(default_factory=list)
    code: Coding
    subject: Reference
    encounter: Reference | None = None
    device: Reference | None = None
    performer: list[Reference] = Field(default_factory=list)
    effectiveDateTime: datetime | None = None
    effectivePeriod: Period | None = None
    issued: datetime | None = None
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


class Observation(ObservationCreate):
    id: str
    meta: Meta = Field(default_factory=Meta)


# ── Condition ──────────────────────────────────────────────────────────────────

class ConditionEvidence(BaseModel):
    code: Coding | None = None
    detail: Reference | None = None


class ConditionCreate(BaseModel):
    resourceType: Literal["Condition"] = "Condition"
    status: str
    verificationStatus: str | None = None
    code: Coding
    subject: Reference
    encounter: Reference | None = None
    recorder: Reference | None = None
    asserter: Reference | None = None
    onsetDateTime: datetime | None = None
    onsetDate: date | None = None
    onsetString: str | None = None
    abatementDate: date | None = None
    recordedDate: datetime | None = None
    severity: str | None = None
    evidence: list[ConditionEvidence] = Field(default_factory=list)
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class Condition(ConditionCreate):
    id: str
    meta: Meta = Field(default_factory=Meta)


# ── MedicationRequest ──────────────────────────────────────────────────────────

class MedicationInfo(BaseModel):
    name: str | None = None
    code: str | None = None
    system: str | None = None
    form: str | None = None
    brand: str | None = None


class DoseQuantity(BaseModel):
    value: float
    unit: str


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
    resourceType: Literal["MedicationRequest"] = "MedicationRequest"
    status: str
    intent: str
    medication: MedicationInfo
    subject: Reference
    encounter: Reference | None = None
    requester: Reference
    dispenser: Reference | None = None
    dosageInstruction: list[DosageInstruction] = Field(default_factory=list)
    dispenseRequest: DispenseRequest | None = None
    controlled: ControlledSubstance | None = None
    vfd: bool = False
    withdrawal: WithdrawalPeriod | None = None
    extraLabel: bool = False
    authoredOn: datetime | None = None
    expiresOn: date | None = None
    note: str | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class MedicationRequest(MedicationRequestCreate):
    id: str
    meta: Meta = Field(default_factory=Meta)
