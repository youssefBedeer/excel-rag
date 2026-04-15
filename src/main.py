from fastapi import FastAPI 
from helpers import get_settings
from routes import data_router
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker



@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    
    # connect to db
    postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"
    
    app.db_engine = create_async_engine(postgres_conn)
    app.db_client = async_sessionmaker(app.db_engine, expire_on_commit=False)

    # Close on finish
    yield
    await app.db_engine.dispose()
    
    
app = FastAPI(lifespan=lifespan) 

@app.get("/")
async def hello_world():
    config = get_settings()
    return {"status": "working",
            "APP_NAME": config.APP_NAME,
            "APP_VERSION": config.APP_VERSION}
    
    
app.include_router(data_router)