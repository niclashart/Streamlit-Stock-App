"""
Configuration module for the Stock Portfolio Assistant backend
"""
import os
from pydantic import BaseSettings, Field
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    # Database settings
    DB_HOST: str = Field(default="localhost", env="DB_HOST")
    DB_PORT: str = Field(default="5432", env="DB_PORT")
    DB_NAME: str = Field(default="stockapp", env="DB_NAME")
    DB_USER: str = Field(default="postgres", env="DB_USER")
    DB_PASSWORD: str = Field(default="postgres", env="DB_PASSWORD")
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # API keys
    DEEPSEEK_API_KEY: str = Field(default="", env="DEEPSEEK_API_KEY")
    
    # JWT Settings
    JWT_SECRET_KEY: str = Field(default="your-secret-key", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=144000, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # API Settings
    API_PREFIX: str = "/api/v1"
    
    # Application settings
    APP_NAME: str = "Stock Portfolio API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "API for Stock Portfolio Assistant"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# For backwards compatibility with older code
API_PREFIX = settings.API_PREFIX
DATABASE_URL = settings.DATABASE_URL
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
DEEPSEEK_API_KEY = settings.DEEPSEEK_API_KEY
