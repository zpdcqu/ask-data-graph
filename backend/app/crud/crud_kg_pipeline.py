from sqlalchemy.orm import Session
from typing import List, Optional, Type
from datetime import datetime

from app.db.models import kg_pipeline_models as models
from app.api.v1.schemas import kg_pipeline_schemas as schemas

def get_kg_pipeline(db: Session, pipeline_id: int) -> Optional[models.KGPipeline]:
    return db.query(models.KGPipeline).filter(models.KGPipeline.id == pipeline_id).first()

def get_kg_pipelines(
    db: Session, skip: int = 0, limit: int = 100, user_id: Optional[int] = None
) -> List[Type[models.KGPipeline]]:
    query = db.query(models.KGPipeline)
    if user_id:
        query = query.filter(models.KGPipeline.created_by_user_id == user_id)
    return query.offset(skip).limit(limit).all()

def create_kg_pipeline(
    db: Session, pipeline: schemas.KGPipelineCreate, user_id: int
) -> models.KGPipeline:
    db_pipeline = models.KGPipeline(
        **pipeline.dict(),
        created_by_user_id=user_id,
        created_at=datetime.utcnow(), # Explicitly set creation and update times
        updated_at=datetime.utcnow()
    )
    db.add(db_pipeline)
    db.commit()
    db.refresh(db_pipeline)
    return db_pipeline

def update_kg_pipeline(
    db: Session, db_obj: models.KGPipeline, obj_in: schemas.KGPipelineUpdate
) -> models.KGPipeline:
    update_data = obj_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db_obj.updated_at = datetime.utcnow()
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_kg_pipeline(db: Session, pipeline_id: int) -> Optional[models.KGPipeline]:
    db_obj = db.query(models.KGPipeline).get(pipeline_id)
    if db_obj:
        # Consider what to do with associated tasks and runs: cascade delete or prevent deletion if they exist.
        # For now, direct delete. SQLAlchemy cascades can be set up in the model relationships.
        db.delete(db_obj)
        db.commit()
    return db_obj 