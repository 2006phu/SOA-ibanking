from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ibanking:ibanking_secret_2026@postgres:5432/payment_db"
    USER_SERVICE_URL: str = "http://user-service:8002"
    TUITION_SERVICE_URL: str = "http://tuition-service:8003"
    OTP_SERVICE_URL: str = "http://otp-service:8005"
    RABBITMQ_URL: str = "amqp://ibanking:rabbitmq_secret_2026@rabbitmq:5672/"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
