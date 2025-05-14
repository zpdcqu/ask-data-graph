from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class DBSchemaMetadata(Base):
    """数据库表结构元数据模型"""
    __tablename__ = "db_schema_metadata"

    id = Column(Integer, primary_key=True, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False)
    db_name = Column(String(100), nullable=False)
    table_name = Column(String(100), nullable=False)
    column_name = Column(String(100), nullable=False)
    data_type = Column(String(50), nullable=False)
    column_size = Column(Integer, nullable=True)
    is_primary_key = Column(Boolean, default=False)
    is_foreign_key = Column(Boolean, default=False)
    referenced_table = Column(String(100), nullable=True)
    referenced_column = Column(String(100), nullable=True)
    column_description = Column(Text, nullable=True)
    sample_values = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_refreshed_at = Column(DateTime, default=datetime.utcnow)
    
    # 建立与数据源的关系
    data_source = relationship("DataSource", back_populates="schema_metadata") 