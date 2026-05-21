from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_SECRET = "dev-secret-key-change-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VHIR_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://vhir:vhir@localhost:5432/vhir"
    secret_key: str = _DEFAULT_SECRET
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8

    dev_token_mode: bool = True  # Disable in production
    server_base_url: str = "http://localhost:8000"
    api_version: str = "v1"

    @model_validator(mode="after")
    def _check_secret(self) -> "Settings":
        if not self.dev_token_mode and self.secret_key == _DEFAULT_SECRET:
            raise ValueError(
                "VHIR_SECRET_KEY must be set to a strong secret when VHIR_DEV_TOKEN_MODE=false"
            )
        return self

    @property
    def api_prefix(self) -> str:
        return f"/{self.api_version}"


settings = Settings()
