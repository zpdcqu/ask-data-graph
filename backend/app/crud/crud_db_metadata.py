from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.db.models.db_metadata_models import DBSchemaMetadata
from app.api.v1.schemas.db_metadata_schemas import DBSchemaMetadataCreate, DBSchemaMetadataUpdate

def get_by_data_source(db: Session, data_source_id: int, skip: int = 0, limit: int = 100):
    """获取指定数据源的所有表结构元数据"""
    return db.query(DBSchemaMetadata).filter(
        DBSchemaMetadata.data_source_id == data_source_id
    ).offset(skip).limit(limit).all()

def get_tables_by_data_source(db: Session, data_source_id: int) -> List[str]:
    """获取指定数据源的所有表名"""
    results = db.query(DBSchemaMetadata.table_name).filter(
        DBSchemaMetadata.data_source_id == data_source_id
    ).distinct().all()
    return [r[0] for r in results]

def get_columns_by_table(db: Session, data_source_id: int, table_name: str) -> List[DBSchemaMetadata]:
    """获取指定表的所有列元数据"""
    return db.query(DBSchemaMetadata).filter(
        DBSchemaMetadata.data_source_id == data_source_id,
        DBSchemaMetadata.table_name == table_name
    ).all()

def create_metadata(db: Session, metadata: DBSchemaMetadataCreate) -> DBSchemaMetadata:
    """创建表结构元数据"""
    db_metadata = DBSchemaMetadata(**metadata.dict())
    db.add(db_metadata)
    db.commit()
    db.refresh(db_metadata)
    return db_metadata

def update_metadata(db: Session, metadata_id: int, metadata: DBSchemaMetadataUpdate) -> Optional[DBSchemaMetadata]:
    """更新表结构元数据"""
    db_metadata = db.query(DBSchemaMetadata).filter(DBSchemaMetadata.id == metadata_id).first()
    if not db_metadata:
        return None
    
    update_data = metadata.dict(exclude_unset=True)
    if update_data:
        update_data["last_refreshed_at"] = datetime.utcnow()
        for key, value in update_data.items():
            setattr(db_metadata, key, value)
        
        db.commit()
        db.refresh(db_metadata)
    return db_metadata

def delete_by_data_source(db: Session, data_source_id: int) -> bool:
    """删除指定数据源的所有元数据"""
    result = db.query(DBSchemaMetadata).filter(
        DBSchemaMetadata.data_source_id == data_source_id
    ).delete()
    db.commit()
    return result > 0 