from .BaseController import BaseController
from models.enums import ResponseEnums
from utils import get_logger
from typing import List
import os



class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)

    def validate_file_type(self, file: str):
        self.logger.debug(f"Validating file type for '{file}'")

        file_ext = os.path.splitext(file)[1][1:]

        if file_ext not in self.app_settings.FILE_ALLOWED_TYPES:
            error_msg = ResponseEnums.ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value
            
            self.logger.warning(
                f"Unsupported file type '{file_ext}' for file '{file}'"
            )
            return False, error_msg

        success_msg = ResponseEnums.ResponseSignal.FILE_VALIDATION_SUCCESS.value
        
        self.logger.info(f"File '{file}' validated successfully")
        return True, success_msg
    
    def get_excel_files_path(self, folder_path) -> List[str]:
        self.logger.debug(f"Scrap excel files from '{folder_path}'")
        
        all_files = [os.path.join(folder_path,file) for file in os.listdir(folder_path)]
        excel_files = [file for file in all_files if file.endswith(("xlsx", "xls"))]

        if not len(excel_files):
            err_msg = "No excel files found in '{folder_path}'"
            self.logger.debug(err_msg)
            return None, err_msg
        else:
            success_msg = f"Excel files found : {excel_files}"
            self.logger.info(success_msg)
            return excel_files
    

