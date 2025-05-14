from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class RelationshipType(str, Enum):
    """表之间的关系类型"""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"
    UNDEFINED = "undefined"

class IdentificationMethod(str, Enum):
    """关系识别方法"""
    AUTO = "auto"
    MANUAL = "manual"

class SyncResponse(BaseModel):
    """同步响应模型"""
    message: str
    status: str
    count: int = 0

class TableRelationshipBase(BaseModel):
    """表关系基本模型"""
    data_source_id: int
    source_table: str
    target_table: str
    relationship_type: RelationshipType = RelationshipType.UNDEFINED
    source_columns: List[str]
    target_columns: List[str]
    is_identified: IdentificationMethod = IdentificationMethod.AUTO
    confidence_score: Optional[int] = None
    description: Optional[str] = None

class TableRelationshipCreate(TableRelationshipBase):
    """创建表关系模型"""
    pass

class TableRelationshipUpdate(BaseModel):
    """更新表关系模型"""
    relationship_type: Optional[RelationshipType] = None
    description: Optional[str] = None
    is_identified: Optional[IdentificationMethod] = None

class TableRelationship(TableRelationshipBase):
    """表关系响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ERDiagramBase(BaseModel):
    """ER图基本模型"""
    data_source_id: int
    name: str
    description: Optional[str] = None
    display_settings: Optional[Dict[str, Any]] = None

class ERDiagramCreate(ERDiagramBase):
    """创建ER图模型"""
    pass

class ERDiagramUpdate(BaseModel):
    """更新ER图模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    layout_data: Optional[Dict[str, Any]] = None
    display_settings: Optional[Dict[str, Any]] = None

class ERDiagram(ERDiagramBase):
    """ER图响应模型"""
    id: int
    layout_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# 前端展示ER图所需的数据结构

class TableColumn(BaseModel):
    """表列信息"""
    name: str
    data_type: str
    size: Optional[int] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    description: Optional[str] = None

class TableNode(BaseModel):
    """表节点"""
    id: str  # 通常是表名
    label: str  # 显示名称，通常是表名
    columns: List[TableColumn]
    position: Optional[Dict[str, float]] = None  # x, y坐标

class RelationshipEdge(BaseModel):
    """关系边"""
    id: str  # 通常是source_table-target_table或加上唯一ID
    source: str  # 源表ID
    target: str  # 目标表ID
    relationship_type: RelationshipType
    source_columns: List[str]
    target_columns: List[str]
    label: Optional[str] = None  # 关系描述标签

class ERDiagramData(BaseModel):
    """完整ER图数据"""
    nodes: List[TableNode]
    edges: List[RelationshipEdge]
    settings: Optional[Dict[str, Any]] = None 