from pydantic import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Server Configuration
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"

    # API Security
    API_KEY: str = ""
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Rate Limiting
    RATE_LIMIT_MAX: int = 100

    # NetSuite Credentials
    NETSUITE_REALM: str = ""
    NETSUITE_CONSUMER_KEY: str = ""
    NETSUITE_CONSUMER_SECRET: str = ""
    NETSUITE_TOKEN_KEY: str = ""
    NETSUITE_TOKEN_SECRET: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
