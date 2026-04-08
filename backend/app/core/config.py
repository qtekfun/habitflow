from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://habitflow:habitflow@localhost:5432/habitflow"
    TEST_DATABASE_URL: str = "postgresql+asyncpg://habitflow:habitflow@localhost:5432/habitflow_test"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    TEMP_TOKEN_EXPIRE_MINUTES: int = 5

    ALLOWED_ORIGINS: str = "http://localhost:5173"
    ALLOW_REGISTRATION: bool = True
    APP_URL: str = "http://localhost:5173"
    DEBUG: bool = False


settings = Settings()
