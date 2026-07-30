from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AdviserOS"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str
    SYNC_DATABASE_URL: str
    SECRET_KEY: str = "change-me"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
