from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, ForeignKey, func, JSON, Text, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.api.v1.schemas.kg_pipeline_schemas import KGPipelineStatus, KGPipelineRunStatus
from app.api.v1.schemas.kg_pipeline_task_schemas import KGPipelineTaskMappingType

class KGPipeline(Base):
    __tablename__ = "kg_pipelines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(1024))
    target_kg_name = Column(String(255), nullable=False)
    schedule = Column(String(100), nullable=True)
    status = Column(SQLEnum(KGPipelineStatus), nullable=False, default=KGPipelineStatus.DRAFT)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    created_by = relationship("User")
    tasks = relationship("KGPipelineTask", back_populates="pipeline", cascade="all, delete-orphan")
    runs = relationship("KGPipelineRun", back_populates="pipeline", cascade="all, delete-orphan")

class KGPipelineTask(Base):
    __tablename__ = "kg_pipeline_tasks"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("kg_pipelines.id"), nullable=False)
    task_order = Column(Integer, nullable=False)
    task_name = Column(String(255), nullable=False)
    source_data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False)
    source_entity_identifier = Column(String(512), nullable=False)
    mapping_type = Column(SQLEnum(KGPipelineTaskMappingType), nullable=False)
    target_label_or_type = Column(String(255), nullable=False)
    field_mappings = Column(JSON, nullable=False)
    filter_conditions = Column(String(1024), nullable=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    pipeline = relationship("KGPipeline", back_populates="tasks")
    source_data_source = relationship("DataSource")

class KGPipelineRun(Base):
    __tablename__ = "kg_pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("kg_pipelines.id"), nullable=False)
    triggered_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Nullable if system-triggered
    
    status = Column(SQLEnum(KGPipelineRunStatus), nullable=False, default=KGPipelineRunStatus.PENDING)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    # Add columns for logs or output summary if needed, e.g., logs = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    pipeline = relationship("KGPipeline", back_populates="runs")
    triggered_by = relationship("User") # User who triggered it 