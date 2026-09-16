from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = (
        "postgresql+asyncpg://ibanking:ibanking_secret_2026@postgres:5432/tuition_db"
    )
    PORT: int = 8003
    SERVICE_NAME: str = "tuition-service"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
