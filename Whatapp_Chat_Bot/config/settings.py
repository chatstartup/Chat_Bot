import os
import logging
from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import model_validator, ConfigDict
from dotenv import load_dotenv, find_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load .env file explicitly with robust path handling
def load_env_file():
    # Try multiple paths in order of preference
    env_paths = [
        find_dotenv(),  # Default location (current directory)
        os.path.join(os.getcwd(), '.env'),  # Explicit current working directory
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),  # Project root
    ]
    
    for path in env_paths:
        if path and os.path.isfile(path):
            logger.debug(f"Found .env file at: {path}")
            load_dotenv(path, override=True)
            logger.debug(f"Loaded .env file from: {path}")
            return True
    
    logger.warning("No .env file found in any location!")
    return False

# Load environment variables
load_env_file()

# Debug environment variables
groq_key = os.getenv('GROQ_API_KEY', '')
logger.debug(f"Environment - GROQ_API_KEY present: {bool(groq_key)}")

"""Application settings"""
class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    GROQ_API_KEY: str
    
    # Model Settings
    GROQ_MODEL: str = "mixtral-8x7b-32768"
    
    # Pinecone Settings
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX: str = ""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields
    )

    @model_validator(mode='after')
    def validate_api_keys(self):
        """Validate that required API keys are present."""
        if not self.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY is not set")
        return self

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    logger.debug(f"Settings loaded with GROQ_API_KEY: {bool(settings.GROQ_API_KEY)}")
    return settings