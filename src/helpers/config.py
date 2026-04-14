from pydantic_settings import BaseSettings, SettingsConfigDict 
from typing import List, Optional 

class Settings(BaseSettings):
    APP_NAME: str 
    APP_VERSION: str 
    
    
def get_settings() -> Settings:
    return Settings()