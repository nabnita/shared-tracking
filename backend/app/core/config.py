from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://expense_user:expense_pass@localhost:5432/expense_db"
    ASYNC_DATABASE_URL: str = "postgresql+asyncpg://expense_user:expense_pass@localhost:5432/expense_db"

    # Application
    SECRET_KEY: str = "change-me-in-production"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Expense Import Service"

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
