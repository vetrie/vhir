"""Adapter configuration from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EZYVET_", case_sensitive=False)

    client_id: str = ""
    client_secret: str = ""
    partner_id: str = ""
    base_url: str = "https://api.ezyvet.com"

    # Clinic-specific field ID overrides (JSON string → parsed at runtime)
    # e.g. '{"species_field_id": "42"}'
    field_overrides: str = "{}"

    # VHIR server to sync into
    vhir_base_url: str = "http://localhost:8000"
    vhir_token: str = ""

    # Polling interval in seconds (used when webhooks are unavailable)
    poll_interval_seconds: int = 60
    # Webhook secret for HMAC verification (optional)
    webhook_secret: str = ""


settings = Settings()
