"""Async VHIR client with typed resource methods, auth helpers, and pagination."""
from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Any

import httpx

from vhir_sdk.exceptions import (
    VhirAuthError,
    VhirConflictError,
    VhirError,
    VhirNotFoundError,
    VhirServerError,
    VhirValidationError,
)
from vhir_sdk.models.resources import (
    AnimalCreate,
    AppointmentCreate,
    ConditionCreate,
    DeviceCreate,
    DeviceMetricCreate,
    EncounterCreate,
    GroupCreate,
    ImmunizationCreate,
    InsuranceClaimCreate,
    LocationCreate,
    MedicationAdministrationCreate,
    MedicationDispenseCreate,
    MedicationRequestCreate,
    MicrochipLookupResponse,
    ObservationCreate,
    OrganizationCreate,
    OwnerCreate,
    PractitionerCreate,
    PractitionerRoleCreate,
    ProcedureCreate,
    ScheduleCreate,
    SlotCreate,
)

TokenRefreshCallback = Callable[[], str]


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    code = response.status_code
    try:
        body = response.json()
    except Exception:
        body = response.text
    msg = f"HTTP {code}: {body}"
    if code == 401 or code == 403:
        raise VhirAuthError(msg, status_code=code)
    if code == 404:
        raise VhirNotFoundError(msg, status_code=code)
    if code == 409:
        raise VhirConflictError(msg, status_code=code)
    if code == 422:
        raise VhirValidationError(msg, detail=body)
    if code >= 500:
        raise VhirServerError(msg, status_code=code)
    raise VhirError(msg, status_code=code)


class VhirClient:
    """Async client for the VHIR REST API.

    Usage::

        async with VhirClient("https://vhir.example.com", token="...") as client:
            animal = await client.create_animal(AnimalCreate(species="canis-familiaris"))
    """

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        token_refresh_callback: TokenRefreshCallback | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._token_refresh_callback = token_refresh_callback
        self._timeout = timeout
        self._http: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> VhirClient:
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
        )
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._http:
            await self._http.aclose()

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:
        token = self._token
        if token_refresh := self._token_refresh_callback:
            token = token_refresh()
            self._token = token
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    async def obtain_dev_token(
        self,
        subject: str = "dev-user",
        role: str = "veterinarian",
        org_id: str = "dev-org",
    ) -> str:
        """Obtain a dev-mode token from /oauth/token and store it on the client."""
        assert self._http is not None, "Use inside async with block"
        resp = await self._http.post(
            "/oauth/token",
            json={"grant_type": "dev", "subject": subject, "role": role, "org_id": org_id},
        )
        _raise_for_status(resp)
        data = resp.json()
        self._token = data["access_token"]
        return self._token

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    def _http_client(self) -> httpx.AsyncClient:
        assert self._http is not None, "Use VhirClient inside an async with block"
        return self._http

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        resp = await self._http_client().get(path, params=params, headers=self._auth_headers())
        _raise_for_status(resp)
        return resp.json()

    async def _post(self, path: str, body: dict[str, Any]) -> Any:
        resp = await self._http_client().post(path, json=body, headers=self._auth_headers())
        _raise_for_status(resp)
        return resp.json()

    async def _put(self, path: str, body: dict[str, Any]) -> Any:
        resp = await self._http_client().put(path, json=body, headers=self._auth_headers())
        _raise_for_status(resp)
        return resp.json()

    async def _delete(self, path: str) -> None:
        resp = await self._http_client().delete(path, headers=self._auth_headers())
        _raise_for_status(resp)

    # ------------------------------------------------------------------
    # Generic CRUD + pagination
    # ------------------------------------------------------------------

    async def search(
        self,
        resource_type: str,
        params: dict[str, Any] | None = None,
        page_size: int = 20,
    ) -> AsyncIterator[dict[str, Any]]:
        """Async generator that yields individual resource dicts across all pages."""
        offset = 0
        while True:
            query: dict[str, Any] = {"_count": page_size, "_offset": offset, **(params or {})}
            bundle = await self._get(f"/v1/{resource_type}", params=query)
            entries: list[dict[str, Any]] = bundle.get("entry", [])
            for entry in entries:
                yield entry.get("resource", entry)
            if len(entries) < page_size:
                break
            offset += page_size

    async def create(self, resource_type: str, data: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = await self._post(f"/v1/{resource_type}", data)
        return result

    async def read(self, resource_type: str, rid: str) -> dict[str, Any]:
        result: dict[str, Any] = await self._get(f"/v1/{resource_type}/{rid}")
        return result

    async def update(self, resource_type: str, rid: str, data: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = await self._put(f"/v1/{resource_type}/{rid}", data)
        return result

    async def delete(self, resource_type: str, rid: str) -> None:
        await self._delete(f"/v1/{resource_type}/{rid}")

    # ------------------------------------------------------------------
    # Typed resource methods
    # ------------------------------------------------------------------

    async def create_animal(self, data: AnimalCreate) -> dict[str, Any]:
        return await self.create("Animal", data.model_dump(exclude_none=True))

    async def read_animal(self, rid: str) -> dict[str, Any]:
        return await self.read("Animal", rid)

    async def update_animal(self, rid: str, data: AnimalCreate) -> dict[str, Any]:
        return await self.update("Animal", rid, data.model_dump(exclude_none=True))

    async def delete_animal(self, rid: str) -> None:
        await self.delete("Animal", rid)

    def search_animals(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("Animal", params)

    # ---- Owner ----

    async def create_owner(self, data: OwnerCreate) -> dict[str, Any]:
        return await self.create("Owner", data.model_dump(exclude_none=True))

    async def read_owner(self, rid: str) -> dict[str, Any]:
        return await self.read("Owner", rid)

    async def update_owner(self, rid: str, data: OwnerCreate) -> dict[str, Any]:
        return await self.update("Owner", rid, data.model_dump(exclude_none=True))

    async def delete_owner(self, rid: str) -> None:
        await self.delete("Owner", rid)

    def search_owners(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("Owner", params)

    # ---- Practitioner ----

    async def create_practitioner(self, data: PractitionerCreate) -> dict[str, Any]:
        return await self.create("Practitioner", data.model_dump(exclude_none=True))

    async def read_practitioner(self, rid: str) -> dict[str, Any]:
        return await self.read("Practitioner", rid)

    async def update_practitioner(self, rid: str, data: PractitionerCreate) -> dict[str, Any]:
        return await self.update("Practitioner", rid, data.model_dump(exclude_none=True))

    async def delete_practitioner(self, rid: str) -> None:
        await self.delete("Practitioner", rid)

    def search_practitioners(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("Practitioner", params)

    # ---- PractitionerRole ----

    async def create_practitioner_role(self, data: PractitionerRoleCreate) -> dict[str, Any]:
        return await self.create("PractitionerRole", data.model_dump(exclude_none=True))

    async def read_practitioner_role(self, rid: str) -> dict[str, Any]:
        return await self.read("PractitionerRole", rid)

    async def update_practitioner_role(
        self, rid: str, data: PractitionerRoleCreate
    ) -> dict[str, Any]:
        return await self.update("PractitionerRole", rid, data.model_dump(exclude_none=True))

    async def delete_practitioner_role(self, rid: str) -> None:
        await self.delete("PractitionerRole", rid)

    def search_practitioner_roles(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("PractitionerRole", params)

    # ---- Organization ----

    async def create_organization(self, data: OrganizationCreate) -> dict[str, Any]:
        return await self.create("Organization", data.model_dump(exclude_none=True))

    async def read_organization(self, rid: str) -> dict[str, Any]:
        return await self.read("Organization", rid)

    async def update_organization(self, rid: str, data: OrganizationCreate) -> dict[str, Any]:
        return await self.update("Organization", rid, data.model_dump(exclude_none=True))

    async def delete_organization(self, rid: str) -> None:
        await self.delete("Organization", rid)

    def search_organizations(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("Organization", params)

    # ---- Encounter ----

    async def create_encounter(self, data: EncounterCreate) -> dict[str, Any]:
        return await self.create("Encounter", data.model_dump(exclude_none=True))

    async def read_encounter(self, rid: str) -> dict[str, Any]:
        return await self.read("Encounter", rid)

    async def update_encounter(self, rid: str, data: EncounterCreate) -> dict[str, Any]:
        return await self.update("Encounter", rid, data.model_dump(exclude_none=True))

    async def delete_encounter(self, rid: str) -> None:
        await self.delete("Encounter", rid)

    def search_encounters(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("Encounter", params)

    # ---- Observation ----

    async def create_observation(self, data: ObservationCreate) -> dict[str, Any]:
        return await self.create("Observation", data.model_dump(exclude_none=True))

    async def read_observation(self, rid: str) -> dict[str, Any]:
        return await self.read("Observation", rid)

    async def update_observation(self, rid: str, data: ObservationCreate) -> dict[str, Any]:
        return await self.update("Observation", rid, data.model_dump(exclude_none=True))

    async def delete_observation(self, rid: str) -> None:
        await self.delete("Observation", rid)

    def search_observations(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("Observation", params)

    # ---- Condition ----

    async def create_condition(self, data: ConditionCreate) -> dict[str, Any]:
        return await self.create("Condition", data.model_dump(exclude_none=True))

    async def read_condition(self, rid: str) -> dict[str, Any]:
        return await self.read("Condition", rid)

    async def update_condition(self, rid: str, data: ConditionCreate) -> dict[str, Any]:
        return await self.update("Condition", rid, data.model_dump(exclude_none=True))

    async def delete_condition(self, rid: str) -> None:
        await self.delete("Condition", rid)

    def search_conditions(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("Condition", params)

    # ---- Immunization ----

    async def create_immunization(self, data: ImmunizationCreate) -> dict[str, Any]:
        return await self.create("Immunization", data.model_dump(exclude_none=True))

    async def read_immunization(self, rid: str) -> dict[str, Any]:
        return await self.read("Immunization", rid)

    async def update_immunization(self, rid: str, data: ImmunizationCreate) -> dict[str, Any]:
        return await self.update("Immunization", rid, data.model_dump(exclude_none=True))

    async def delete_immunization(self, rid: str) -> None:
        await self.delete("Immunization", rid)

    def search_immunizations(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("Immunization", params)

    # ---- MedicationRequest ----

    async def create_medication_request(self, data: MedicationRequestCreate) -> dict[str, Any]:
        return await self.create("MedicationRequest", data.model_dump(exclude_none=True))

    async def read_medication_request(self, rid: str) -> dict[str, Any]:
        return await self.read("MedicationRequest", rid)

    async def update_medication_request(
        self, rid: str, data: MedicationRequestCreate
    ) -> dict[str, Any]:
        return await self.update("MedicationRequest", rid, data.model_dump(exclude_none=True))

    async def delete_medication_request(self, rid: str) -> None:
        await self.delete("MedicationRequest", rid)

    def search_medication_requests(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("MedicationRequest", params)

    # ---- MedicationDispense ----

    async def create_medication_dispense(self, data: MedicationDispenseCreate) -> dict[str, Any]:
        return await self.create("MedicationDispense", data.model_dump(exclude_none=True))

    async def read_medication_dispense(self, rid: str) -> dict[str, Any]:
        return await self.read("MedicationDispense", rid)

    async def update_medication_dispense(
        self, rid: str, data: MedicationDispenseCreate
    ) -> dict[str, Any]:
        return await self.update("MedicationDispense", rid, data.model_dump(exclude_none=True))

    async def delete_medication_dispense(self, rid: str) -> None:
        await self.delete("MedicationDispense", rid)

    def search_medication_dispenses(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("MedicationDispense", params)

    # ---- MedicationAdministration ----

    async def create_medication_administration(
        self, data: MedicationAdministrationCreate
    ) -> dict[str, Any]:
        return await self.create("MedicationAdministration", data.model_dump(exclude_none=True))

    async def read_medication_administration(self, rid: str) -> dict[str, Any]:
        return await self.read("MedicationAdministration", rid)

    async def update_medication_administration(
        self, rid: str, data: MedicationAdministrationCreate
    ) -> dict[str, Any]:
        return await self.update(
            "MedicationAdministration", rid, data.model_dump(exclude_none=True)
        )

    async def delete_medication_administration(self, rid: str) -> None:
        await self.delete("MedicationAdministration", rid)

    def search_medication_administrations(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("MedicationAdministration", params)

    # ---- Device ----

    async def create_device(self, data: DeviceCreate) -> dict[str, Any]:
        return await self.create("Device", data.model_dump(exclude_none=True))

    async def read_device(self, rid: str) -> dict[str, Any]:
        return await self.read("Device", rid)

    async def update_device(self, rid: str, data: DeviceCreate) -> dict[str, Any]:
        return await self.update("Device", rid, data.model_dump(exclude_none=True))

    async def delete_device(self, rid: str) -> None:
        await self.delete("Device", rid)

    def search_devices(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("Device", params)

    # ---- DeviceMetric ----

    async def create_device_metric(self, data: DeviceMetricCreate) -> dict[str, Any]:
        return await self.create("DeviceMetric", data.model_dump(exclude_none=True))

    async def read_device_metric(self, rid: str) -> dict[str, Any]:
        return await self.read("DeviceMetric", rid)

    async def update_device_metric(self, rid: str, data: DeviceMetricCreate) -> dict[str, Any]:
        return await self.update("DeviceMetric", rid, data.model_dump(exclude_none=True))

    async def delete_device_metric(self, rid: str) -> None:
        await self.delete("DeviceMetric", rid)

    def search_device_metrics(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("DeviceMetric", params)

    # ---- Group ----

    async def create_group(self, data: GroupCreate) -> dict[str, Any]:
        return await self.create("Group", data.model_dump(exclude_none=True))

    async def read_group(self, rid: str) -> dict[str, Any]:
        return await self.read("Group", rid)

    async def update_group(self, rid: str, data: GroupCreate) -> dict[str, Any]:
        return await self.update("Group", rid, data.model_dump(exclude_none=True))

    async def delete_group(self, rid: str) -> None:
        await self.delete("Group", rid)

    def search_groups(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("Group", params)

    # ---- InsuranceClaim ----

    async def create_insurance_claim(self, data: InsuranceClaimCreate) -> dict[str, Any]:
        return await self.create("InsuranceClaim", data.model_dump(exclude_none=True))

    async def read_insurance_claim(self, rid: str) -> dict[str, Any]:
        return await self.read("InsuranceClaim", rid)

    async def update_insurance_claim(
        self, rid: str, data: InsuranceClaimCreate
    ) -> dict[str, Any]:
        return await self.update("InsuranceClaim", rid, data.model_dump(exclude_none=True))

    async def delete_insurance_claim(self, rid: str) -> None:
        await self.delete("InsuranceClaim", rid)

    def search_insurance_claims(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("InsuranceClaim", params)

    # ---- Appointment ----

    async def create_appointment(self, data: AppointmentCreate) -> dict[str, Any]:
        return await self.create("Appointment", data.model_dump(exclude_none=True))

    async def read_appointment(self, rid: str) -> dict[str, Any]:
        return await self.read("Appointment", rid)

    async def update_appointment(self, rid: str, data: AppointmentCreate) -> dict[str, Any]:
        return await self.update("Appointment", rid, data.model_dump(exclude_none=True))

    async def delete_appointment(self, rid: str) -> None:
        await self.delete("Appointment", rid)

    def search_appointments(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("Appointment", params)

    # ---- Schedule ----

    async def create_schedule(self, data: ScheduleCreate) -> dict[str, Any]:
        return await self.create("Schedule", data.model_dump(exclude_none=True))

    async def read_schedule(self, rid: str) -> dict[str, Any]:
        return await self.read("Schedule", rid)

    async def update_schedule(self, rid: str, data: ScheduleCreate) -> dict[str, Any]:
        return await self.update("Schedule", rid, data.model_dump(exclude_none=True))

    async def delete_schedule(self, rid: str) -> None:
        await self.delete("Schedule", rid)

    def search_schedules(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("Schedule", params)

    # ---- Slot ----

    async def create_slot(self, data: SlotCreate) -> dict[str, Any]:
        return await self.create("Slot", data.model_dump(exclude_none=True))

    async def read_slot(self, rid: str) -> dict[str, Any]:
        return await self.read("Slot", rid)

    async def update_slot(self, rid: str, data: SlotCreate) -> dict[str, Any]:
        return await self.update("Slot", rid, data.model_dump(exclude_none=True))

    async def delete_slot(self, rid: str) -> None:
        await self.delete("Slot", rid)

    def search_slots(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("Slot", params)

    # ---- Location ----

    async def create_location(self, data: LocationCreate) -> dict[str, Any]:
        return await self.create("Location", data.model_dump(exclude_none=True))

    async def read_location(self, rid: str) -> dict[str, Any]:
        return await self.read("Location", rid)

    async def update_location(self, rid: str, data: LocationCreate) -> dict[str, Any]:
        return await self.update("Location", rid, data.model_dump(exclude_none=True))

    async def delete_location(self, rid: str) -> None:
        await self.delete("Location", rid)

    def search_locations(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("Location", params)

    # ---- Procedure ----

    async def create_procedure(self, data: ProcedureCreate) -> dict[str, Any]:
        return await self.create("Procedure", data.model_dump(exclude_none=True))

    async def read_procedure(self, rid: str) -> dict[str, Any]:
        return await self.read("Procedure", rid)

    async def update_procedure(self, rid: str, data: ProcedureCreate) -> dict[str, Any]:
        return await self.update("Procedure", rid, data.model_dump(exclude_none=True))

    async def delete_procedure(self, rid: str) -> None:
        await self.delete("Procedure", rid)

    def search_procedures(self, **params: Any) -> AsyncIterator[dict[str, Any]]:
        return self.search("Procedure", params)

    # ---- System operations ----

    async def lookup_microchip(self, chip_id: str) -> MicrochipLookupResponse:
        data = await self._post("/v1/$lookup-microchip", {"chipId": chip_id})
        return MicrochipLookupResponse.model_validate(data)

    async def get_capability_statement(self) -> dict[str, Any]:
        result: dict[str, Any] = await self._get("/v1/metadata")
        return result


# Convenience: collect all pages from a search into a list
async def collect(iterator: AsyncIterator[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item async for item in iterator]
