from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class KGPipelineStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"

class KGPipelineBase(BaseModel):
    name: str
    description: Optional[str] = None
    target_kg_name: str # Name of the graph space in NebulaGraph, for example
    schedule: Optional[str] = None # Cron expression for scheduling

class KGPipelineCreate(KGPipelineBase):
    pass

class KGPipelineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_kg_name: Optional[str] = None
    schedule: Optional[str] = None
    status: Optional[KGPipelineStatus] = None

class KGPipelineInDBBase(KGPipelineBase):
    id: int
    created_by_user_id: int
    status: KGPipelineStatus = KGPipelineStatus.DRAFT
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class KGPipeline(KGPipelineInDBBase):
    pass

# Schemas for Pipeline Runs (will be used later)
class KGPipelineRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class KGPipelineRunBase(BaseModel):
    pipeline_id: int
    triggered_by_user_id: Optional[int] = None # Can be system-triggered
    # remarks: Optional[str] = None

class KGPipelineRunCreate(KGPipelineRunBase):
    pass # Status will be set internally

class KGPipelineRun(KGPipelineRunBase):
    id: int
    status: KGPipelineRunStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    # Add output or log summary if needed
    # task_details: Optional[List[Any]] = None # For detailed task statuses in a run

    class Config:
        orm_mode = True 