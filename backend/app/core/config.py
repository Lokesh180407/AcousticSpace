from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # General
    PROJECT_NAME: str = "AcousticSpace"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/acousticspace"

    # JWT
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_ENV"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Guest sessions
    GUEST_ID_COOKIE_NAME: str = "guest_id"
    GUEST_ID_HEADER_NAME: str = "X-Guest-Id"

    # File storage
    UPLOAD_DIR: str = "storage/audio"
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_AUDIO_CONTENT_TYPES: tuple = (
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/flac",
        "audio/ogg",
        "audio/webm",
    )

    model_config = SettingsConfigDict(env_file="app/.env", env_file_encoding="utf-8")


settings = Settings()
