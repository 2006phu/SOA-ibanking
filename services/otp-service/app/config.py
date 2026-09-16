from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVICE_NAME: str = "otp-service"
    PORT: int = 8005
    DATABASE_URL: str = (
        "postgresql+asyncpg://ibanking:ibanking_secret_2026@postgres:5432/otp_db"
    )
    RABBITMQ_URL: str = "amqp://ibanking:rabbitmq_secret_2026@rabbitmq:5672/"
    OTP_EXPIRATION_MINUTES: int = 5
    OTP_LENGTH: int = 6

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
