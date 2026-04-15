from pydantic_settings import BaseSettings, SettingsConfigDict 
from typing import List, Optional 

class Settings(BaseSettings):
    APP_NAME: str 
    APP_VERSION: str 
    
    FILE_ALLOWED_TYPES: List[str]
    
    # DATABASE
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_MAIN_DATABASE: str
    
    model_config = SettingsConfigDict(env_file=".env")
    
def get_settings() -> Settings:
    return Settings()