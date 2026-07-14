from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    env: str = "development"
    app_name: str = "Acoustic Space"
    api_prefix: str = "/api/v1"

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    jwt_access_secret: str
    jwt_refresh_secret: str
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 2592000

    bcrypt_rounds: int = 12

    database_url: str

    uploads_base_path: str = "./uploads"

    log_level: str = "INFO"

    rate_limit_enabled: bool = False

    email_verification_enabled: bool = False
    email_from: str = "no-reply@example.com"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

