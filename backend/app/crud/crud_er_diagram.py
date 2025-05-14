from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.db.models.er_diagram_models import TableRelationship, ERDiagram
from app.api.v1.schemas.er_diagram_schemas import TableRelationshipCreate, TableRelationshipUpdate, ERDiagramCreate, ERDiagramUpdate

# TableRelationship CRUD操作

def get_relationships_by_data_source(db: Session, data_source_id: int, skip: int = 0, limit: int = 100):
    """获取指定数据源的所有表关系"""
    return db.query(TableRelationship).filter(
        TableRelationship.data_source_id == data_source_id
    ).offset(skip).limit(limit).all()

def get_relationship(db: Session, relationship_id: int):
    """获取指定ID的表关系"""
    return db.query(TableRelationship).filter(
        TableRelationship.id == relationship_id
    ).first()

def create_relationship(db: Session, relationship: TableRelationshipCreate):
    """创建表关系"""
    db_relationship = TableRelationship(**relationship.dict())
    db.add(db_relationship)
    db.commit()
    db.refresh(db_relationship)
    return db_relationship

def update_relationship(db: Session, relationship_id: int, relationship: TableRelationshipUpdate):
    """更新表关系"""
    db_relationship = get_relationship(db, relationship_id)
    if db_relationship is None:
        return None
    
    update_data = relationship.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_relationship, key, value)
    
    db_relationship.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_relationship)
    return db_relationship

def delete_relationship(db: Session, relationship_id: int):
    """删除表关系"""
    db_relationship = get_relationship(db, relationship_id)
    if db_relationship is None:
        return False
    
    db.delete(db_relationship)
    db.commit()
    return True

def delete_relationships_by_data_source(db: Session, data_source_id: int):
    """删除指定数据源的所有表关系"""
    result = db.query(TableRelationship).filter(
        TableRelationship.data_source_id == data_source_id
    ).delete()
    db.commit()
    return result > 0

# ERDiagram CRUD操作

def get_diagrams_by_data_source(db: Session, data_source_id: int, skip: int = 0, limit: int = 100):
    """获取指定数据源的所有ER图"""
    return db.query(ERDiagram).filter(
        ERDiagram.data_source_id == data_source_id
    ).offset(skip).limit(limit).all()

def get_diagram(db: Session, diagram_id: int):
    """获取指定ID的ER图"""
    return db.query(ERDiagram).filter(
        ERDiagram.id == diagram_id
    ).first()

def create_diagram(db: Session, diagram: ERDiagramCreate):
    """创建ER图"""
    db_diagram = ERDiagram(**diagram.dict())
    db.add(db_diagram)
    db.commit()
    db.refresh(db_diagram)
    return db_diagram

def update_diagram(db: Session, diagram_id: int, diagram: ERDiagramUpdate):
    """更新ER图"""
    db_diagram = get_diagram(db, diagram_id)
    if db_diagram is None:
        return None
    
    update_data = diagram.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_diagram, key, value)
    
    db_diagram.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_diagram)
    return db_diagram

def delete_diagram(db: Session, diagram_id: int):
    """删除ER图"""
    db_diagram = get_diagram(db, diagram_id)
    if db_diagram is None:
        return False
    
    db.delete(db_diagram)
    db.commit()
    return True 