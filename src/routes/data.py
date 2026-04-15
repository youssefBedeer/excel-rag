from fastapi import APIRouter, Request
from controllers import DataController
import os

data_router = APIRouter(prefix="/api/v1/data", 
                        tags=["data", "api_v1"])

@data_router.get("/files")
async def get_files():
    data_controller = DataController()
    assets_path = data_controller.assets_dir
    os.makedirs(assets_path, exist_ok=True)
    excel_files = data_controller.get_excel_files_path(folder_path=assets_path)

    return {
        "Assets_dir": assets_path,
        "Excel_files": excel_files}
    
@data_router.get("/filldata")
async def fill_data(request: Request):
    data_controller = DataController()
    assets_path = data_controller.assets_dir
    os.makedirs(assets_path, exist_ok=True)
    excel_files = data_controller.get_excel_files_path(folder_path=assets_path)
    
    await data_controller.insert_excel_into_db(
        files=excel_files,
        async_engine=request.app.db_engine,
        async_session_maker=request.app.db_client
    )