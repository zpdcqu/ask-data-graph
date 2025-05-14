from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DBSchemaMetadataBase(BaseModel):
    data_source_id: int
    db_name: str
    table_name: str
    column_name: str
    data_type: str
    is_primary_key: bool = False
    is_foreign_key: bool = False
    referenced_table: Optional[str] = None
    referenced_column: Optional[str] = None
    column_description: Optional[str] = None

class DBSchemaMetadataCreate(DBSchemaMetadataBase):
    pass

class DBSchemaMetadataUpdate(BaseModel):
    column_description: Optional[str] = None
    sample_values: Optional[List[Any]] = None

class DBSchemaMetadata(DBSchemaMetadataBase):
    id: int
    column_size: Optional[int] = None
    sample_values: Optional[List[Any]] = None
    created_at: datetime
    last_refreshed_at: datetime
    
    class Config:
        orm_mode = True

class SyncResponse(BaseModel):
    message: str
    status: str
    tables_count: int = 0
    columns_count: int = 0 