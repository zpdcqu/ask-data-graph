from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base_class import Base

class RelationshipType(str, enum.Enum):
    """表之间的关系类型"""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"
    UNDEFINED = "undefined"

class TableRelationship(Base):
    """表之间的关系模型"""
    __tablename__ = "table_relationships"

    id = Column(Integer, primary_key=True, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False)
    source_table = Column(String(100), nullable=False)
    target_table = Column(String(100), nullable=False)
    relationship_type = Column(String(20), nullable=False, default=RelationshipType.UNDEFINED)
    source_columns = Column(JSON, nullable=False)  # 关联的源表列，JSON数组
    target_columns = Column(JSON, nullable=False)  # 关联的目标表列，JSON数组
    is_identified = Column(String(20), nullable=False, default="auto") # auto / manual
    confidence_score = Column(Integer, nullable=True)  # 0-100 置信度
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联到数据源
    data_source = relationship("DataSource", back_populates="table_relationships")

class ERDiagram(Base):
    """ER图配置模型"""
    __tablename__ = "er_diagrams"
    
    id = Column(Integer, primary_key=True, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    layout_data = Column(JSON, nullable=True)  # 图布局数据
    display_settings = Column(JSON, nullable=True)  # 显示设置，如颜色、可见性等
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联到数据源
    data_source = relationship("DataSource", back_populates="er_diagrams") 