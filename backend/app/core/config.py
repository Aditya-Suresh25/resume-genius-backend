import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    USE_REAL_GITHUB: bool = os.getenv("USE_REAL_GITHUB", "False").lower() == "true"
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    class Config:
        env_file = ".env"

settings = Settings()
