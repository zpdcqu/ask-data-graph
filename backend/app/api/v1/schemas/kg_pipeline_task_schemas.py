from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

class KGPipelineTaskMappingType(str, Enum):
    NODE = "node"
    RELATIONSHIP = "relationship"

class KGPipelineTaskBase(BaseModel):
    task_order: int
    task_name: str
    source_data_source_id: int # ID of a DataSource model
    source_entity_identifier: str # e.g., table name, API endpoint path
    mapping_type: KGPipelineTaskMappingType
    target_label_or_type: str # Node label or Relationship type in KG
    field_mappings: Dict[str, Any] # Defines how source fields map to KG properties
                                   # Example for Node: {"source_col1": {"target_property": "prop1", "is_id": True}, "source_col2": {"target_property": "prop2"}}
                                   # Example for Relationship: {"from_node_id_col": "src_id_col", "to_node_id_col": "dst_id_col", "rel_prop_col": "prop1"}
    filter_conditions: Optional[str] = None # e.g., SQL WHERE clause for source data
    is_enabled: bool = True

class KGPipelineTaskCreate(KGPipelineTaskBase):
    pipeline_id: int # Associate with a KGPipeline

class KGPipelineTaskUpdate(BaseModel):
    task_order: Optional[int] = None
    task_name: Optional[str] = None
    source_data_source_id: Optional[int] = None
    source_entity_identifier: Optional[str] = None
    mapping_type: Optional[KGPipelineTaskMappingType] = None
    target_label_or_type: Optional[str] = None
    field_mappings: Optional[Dict[str, Any]] = None
    filter_conditions: Optional[str] = None
    is_enabled: Optional[bool] = None

class KGPipelineTaskInDBBase(KGPipelineTaskBase):
    id: int
    pipeline_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class KGPipelineTask(KGPipelineTaskInDBBase):
    pass 