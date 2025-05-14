from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import Base
from app.api.v1.schemas.data_source_schemas import DataSourceType, DataSourceStatus # For Enum values

class DataSourceType(str, enum.Enum):
    MYSQL = "MySQL"
    POSTGRESQL = "PostgreSQL"
    CSV = "CSV"
    EXCEL = "Excel"
    API = "API"

class DataSource(Base):
    """数据源模型"""
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    # Store connection_params as JSON. Sensitive info should be handled carefully.
    # Consider encryption for sensitive fields within the JSON or using a secrets manager.
    connection_params = Column(JSON, nullable=False)
    
    status = Column(String(20), default="pending_test")
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_tested_at = Column(DateTime, nullable=True)

    created_by = relationship("User") #, back_populates="data_sources")
    
    # 添加与DBSchemaMetadata的关系
    schema_metadata = relationship("DBSchemaMetadata", back_populates="data_source", cascade="all, delete-orphan")
    
    # 添加与TableRelationship的关系
    table_relationships = relationship("TableRelationship", back_populates="data_source", cascade="all, delete-orphan")
    
    # 添加与ERDiagram的关系
    er_diagrams = relationship("ERDiagram", back_populates="data_source", cascade="all, delete-orphan") 