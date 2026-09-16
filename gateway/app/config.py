from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    JWT_SECRET_KEY: str = "ibanking-jwt-super-secret-key-2026-tdtu"
    JWT_ALGORITHM: str = "HS256"
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    USER_SERVICE_URL: str = "http://user-service:8002"
    TUITION_SERVICE_URL: str = "http://tuition-service:8003"
    PAYMENT_SERVICE_URL: str = "http://payment-service:8004"
    OTP_SERVICE_URL: str = "http://otp-service:8005"

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
