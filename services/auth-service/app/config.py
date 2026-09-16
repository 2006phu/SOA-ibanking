from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ibanking:ibanking_secret_2026@postgres:5432/auth_db"
    JWT_SECRET_KEY: str = "ibanking-jwt-super-secret-key-2026-tdtu"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    PORT: int = 8001
    SERVICE_NAME: str = "auth-service"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
