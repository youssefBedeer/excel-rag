from fastapi import FastAPI 
from helpers import get_settings
from routes import data_router


app = FastAPI() 

@app.get("/")
async def hello_world():
    config = get_settings()
    return {"status": "working",
            "APP_NAME": config.APP_NAME,
            "APP_VERSION": config.APP_VERSION}
    
    
app.include_router(data_router)