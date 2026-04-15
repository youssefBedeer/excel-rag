from .BaseController import BaseController
from models.enums import ResponseEnums
from utils import get_logger
from typing import List
import os
import pandas as pd
from sqlalchemy import Table, Column, String, Integer, Float, Boolean, MetaData, insert
from sqlalchemy.ext.asyncio import AsyncEngine
import asyncio



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
    
    def get_excel_files_path(self, folder_path) -> list[str]:
        import os

        self.logger.debug(f"Scrap excel files from '{folder_path}'")

        # check folder exists
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        # list all files
        all_files = [
            os.path.join(folder_path, file)
            for file in os.listdir(folder_path)
        ]

        # filter only valid excel files
        excel_files = [
            file for file in all_files
            if file.lower().endswith((".xlsx", ".xls"))   # handle uppercase
            and not os.path.basename(file).startswith("~$")  # temp files
            and os.path.getsize(file) > 0   # avoid empty files (your previous bug)
        ]

        if not excel_files:
            err_msg = f"No valid excel files found in '{folder_path}'"
            self.logger.warning(err_msg)
            return []

        self.logger.info(f"Excel files found: {excel_files}")
        return excel_files
        
    def _infer_column_type(self, series):
        """Infer SQLAlchemy column type from pandas Series."""
        # For numeric dtypes
        if pd.api.types.is_integer_dtype(series):
            return Integer
        elif pd.api.types.is_float_dtype(series):
            return Float
        elif pd.api.types.is_bool_dtype(series):
            return Boolean
        
        # For object dtype, try to infer the actual type
        if series.dtype == 'object':
            # Drop NaN values for inference
            non_null = series.dropna()
            if len(non_null) == 0:
                return String(255)
            
            # Try to convert to numeric
            try:
                pd.to_numeric(non_null)
                # Check if all values are integers
                if all(isinstance(x, (int, float)) and (isinstance(x, int) or x == int(x)) for x in non_null):
                    return Integer
                else:
                    return Float
            except (ValueError, TypeError):
                pass
            
            return String(255)
        
        return String(255)

    def _convert_record_types(self, record, table):
        """Convert record values to match table column types."""
        converted = {}
        for col_name, value in record.items():
            if pd.isna(value):
                converted[col_name] = None
            else:
                # Get the column from the table
                col = table.columns.get(col_name)
                if col is not None:
                    # Convert based on column type
                    from sqlalchemy import Integer, Float, Boolean, String
                    if isinstance(col.type, Integer):
                        converted[col_name] = int(value) if value is not None else None
                    elif isinstance(col.type, Float):
                        converted[col_name] = float(value) if value is not None else None
                    elif isinstance(col.type, Boolean):
                        converted[col_name] = bool(value) if value is not None else None
                    else:
                        converted[col_name] = str(value) if value is not None else None
                else:
                    converted[col_name] = value
        return converted

    async def _get_existing_records(self, session, table) -> List[dict]:
        """Fetch all existing records from the table."""
        try:
            from sqlalchemy import select
            result = await session.execute(select(table))
            rows = result.fetchall()
            return [row._mapping if hasattr(row, '_mapping') else dict(row) for row in rows]
        except Exception:
            # Table doesn't exist or is empty
            return []

    async def insert_excel_into_db(self, files: List[str], async_engine, async_session_maker, batch_size: int = 1000):
        """Insert Excel files into database only if data has changed.
        
        Args:
            files: List of Excel file paths
            async_engine: SQLAlchemy async engine
            async_session_maker: SQLAlchemy async session maker
            batch_size: Number of records to insert per batch (default: 1000)
        """
        for excel_file in files:
            try:
                # Read Excel file
                df = pd.read_excel(excel_file)
                table_name = os.path.splitext(os.path.basename(excel_file))[0]
                
                self.logger.info(f"Processing data from '{excel_file}' for table '{table_name}'")
                
                # Create table dynamically based on DataFrame columns
                metadata = MetaData()
                columns = []
                
                for col_name in df.columns:
                    col_type = self._infer_column_type(df[col_name])
                    columns.append(Column(col_name, col_type))
                
                table = Table(table_name, metadata, *columns, extend_existing=True)
                
                # Create table using engine connection
                async with async_engine.begin() as conn:
                    await conn.run_sync(metadata.create_all)
                
                # Get existing records from database
                async with async_session_maker() as session:
                    existing_records = await self._get_existing_records(session, table)
                
                # Convert existing records to a set of tuples for comparison
                existing_set = set()
                for record in existing_records:
                    record_tuple = tuple(sorted(record.items()))
                    existing_set.add(record_tuple)
                
                # Prepare new records and identify changes
                all_records = df.to_dict('records')
                new_records_to_insert = []
                
                for record in all_records:
                    converted_record = self._convert_record_types(record, table)
                    record_tuple = tuple(sorted(converted_record.items()))
                    
                    # Only add record if it doesn't exist in database
                    if record_tuple not in existing_set:
                        new_records_to_insert.append(converted_record)
                
                if not new_records_to_insert:
                    self.logger.info(f"No changes detected for '{table_name}'. Skipping insertion.")
                    continue
                
                # Insert only new/changed records in batches
                total_new = len(new_records_to_insert)
                self.logger.info(f"Found {total_new} new/changed records to insert into '{table_name}'")
                
                for batch_start in range(0, total_new, batch_size):
                    batch_end = min(batch_start + batch_size, total_new)
                    batch = new_records_to_insert[batch_start:batch_end]
                    
                    async with async_session_maker() as session:
                        async with session.begin():
                            for record in batch:
                                await session.execute(insert(table).values(**record))
                    
                    self.logger.info(f"Inserted batch {batch_start + 1}-{batch_end} of {total_new} new records into '{table_name}'")
                
                self.logger.info(f"Successfully inserted {total_new} new/changed records into '{table_name}'")
            except Exception as e:
                self.logger.error(f"Error processing data from '{excel_file}': {str(e)}")
                raise
    

