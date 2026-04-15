from helpers.config import get_settings 
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

class BaseDataModel:
    def __init__(self, db_client: async_sessionmaker[AsyncSession]):
        self.app_settings = get_settings() 
        self.db_client = db_client