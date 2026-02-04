"""SEO Article Generator - Configuration settings."""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    
    # SerpAPI Configuration
    serpapi_api_key: str = ""
    
    # Database Configuration
    database_url: str = "sqlite:///./data/jobs.db"
    
    # Application Settings
    debug: bool = False
    log_level: str = "INFO"
    
    # Content Generation Settings
    default_word_count: int = 1500
    default_language: str = "en"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
