from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVICE_NAME: str = "user-service"
    PORT: int = 8002
    HOST: str = "0.0.0.0"
    DATABASE_URL: str = (
        "postgresql+asyncpg://ibanking:ibanking_secret_2026@postgres:5432/user_db"
    )
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
