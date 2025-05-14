from sqlalchemy import Column, Integer, String, Enum as SQLEnum, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.api.v1.schemas.data_source_schemas import DataSourceType, DataSourceStatus # For Enum values

class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    type = Column(SQLEnum(DataSourceType), nullable=False)
    description = Column(String(1024))
    # Store connection_params as JSON. Sensitive info should be handled carefully.
    # Consider encryption for sensitive fields within the JSON or using a secrets manager.
    connection_params = Column(JSON, nullable=False)
    
    status = Column(SQLEnum(DataSourceStatus), nullable=False, default=DataSourceStatus.PENDING_TEST)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_tested_at = Column(DateTime, nullable=True)

    created_by = relationship("User") #, back_populates="data_sources") 