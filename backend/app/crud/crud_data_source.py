from sqlalchemy.orm import Session
from typing import List, Optional, Type

from app.db.models import data_source_models as models
from app.api.v1.schemas import data_source_schemas as schemas
from datetime import datetime

def get_data_source(db: Session, data_source_id: int) -> Optional[models.DataSource]:
    return db.query(models.DataSource).filter(models.DataSource.id == data_source_id).first()

def get_data_sources( 
    db: Session, skip: int = 0, limit: int = 100
) -> List[Type[models.DataSource]]: # Adjusted for list of model instances
    return db.query(models.DataSource).offset(skip).limit(limit).all()

def get_data_sources_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[Type[models.DataSource]]: # Adjusted for list of model instances
    return (
        db.query(models.DataSource)
        .filter(models.DataSource.created_by_user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_data_source(
    db: Session, data_source: schemas.DataSourceCreate, user_id: int
) -> models.DataSource:
    db_data_source = models.DataSource(
        **data_source.dict(),
        created_by_user_id=user_id,
        created_at=datetime.utcnow() # Ensure created_at is set
    )
    db.add(db_data_source)
    db.commit()
    db.refresh(db_data_source)
    return db_data_source

def update_data_source(
    db: Session, db_obj: models.DataSource, obj_in: schemas.DataSourceUpdate
) -> models.DataSource:
    update_data = obj_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db_obj.updated_at = datetime.utcnow() # Ensure updated_at is set
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_data_source(db: Session, data_source_id: int) -> Optional[models.DataSource]:
    db_obj = db.query(models.DataSource).get(data_source_id)
    if db_obj:
        db.delete(db_obj)
        db.commit()
    return db_obj 