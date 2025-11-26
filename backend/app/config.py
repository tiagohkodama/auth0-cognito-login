from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Application
    APP_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str

    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AWS Cognito
    AWS_REGION: str = "us-east-1"
    COGNITO_USER_POOL_ID: str
    COGNITO_CLIENT_ID: str
    COGNITO_CLIENT_SECRET: str
    COGNITO_DOMAIN: str
    COGNITO_CALLBACK_URL: str

    # Auth0 (Research Catalog)
    AUTH0_RESEARCH_DOMAIN: str
    AUTH0_RESEARCH_CLIENT_ID: str
    AUTH0_RESEARCH_CLIENT_SECRET: str
    AUTH0_RESEARCH_CALLBACK_URL: str

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Global settings instance
settings = Settings()
