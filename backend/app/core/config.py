from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://expense_user:expense_pass@localhost:5432/expense_db"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        # Render provides postgres://, asyncpg needs postgresql+asyncpg://
        return self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://").replace("postgresql://", "postgresql+asyncpg://")

    # Application
    SECRET_KEY: str = "change-me-in-production"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Expense Import Service"

    # CORS — comma-separated string in .env to avoid pydantic-settings JSON parse issues
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
