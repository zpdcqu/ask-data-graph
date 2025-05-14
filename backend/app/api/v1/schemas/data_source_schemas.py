from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

class DataSourceType(str, Enum):
    MYSQL = "MySQL"
    POSTGRESQL = "PostgreSQL"
    CSV = "CSV"
    EXCEL = "Excel"
    API = "API"
    # Add other types as needed

class DataSourceStatus(str, Enum):
    PENDING_TEST = "pending_test"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class DataSourceBase(BaseModel):
    name: str
    type: DataSourceType
    description: Optional[str] = None
    connection_params: Dict[str, Any] # Flexible for different types

class DataSourceCreate(DataSourceBase):
    pass

class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[DataSourceType] = None
    description: Optional[str] = None
    connection_params: Optional[Dict[str, Any]] = None
    status: Optional[DataSourceStatus] = None # Allow status update, e.g., after test

class DataSourceInDBBase(DataSourceBase):
    id: int
    created_by_user_id: int
    status: DataSourceStatus = DataSourceStatus.PENDING_TEST
    created_at: datetime
    last_tested_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class DataSource(DataSourceInDBBase):
    pass

class DataSourceTestResult(BaseModel):
    status: str # "success" or "failed"
    message: Optional[str] = None 