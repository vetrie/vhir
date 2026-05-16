from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VHIR_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://vhir:vhir@localhost:5432/vhir"
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8

    dev_token_mode: bool = True  # Disable in production
    server_base_url: str = "http://localhost:8000"
    api_version: str = "v1"

    @property
    def api_prefix(self) -> str:
        return f"/{self.api_version}"


settings = Settings()
