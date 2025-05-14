from sqlalchemy.orm import Session
from typing import List, Optional, Type
from datetime import datetime

from app.db.models import kg_pipeline_models as models # KGPipelineRun is in here
from app.api.v1.schemas import kg_pipeline_schemas as schemas

def get_kg_pipeline_run(db: Session, run_id: int) -> Optional[models.KGPipelineRun]:
    return db.query(models.KGPipelineRun).filter(models.KGPipelineRun.id == run_id).first()

def get_kg_pipeline_runs(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    pipeline_id: Optional[int] = None,
    status: Optional[schemas.KGPipelineRunStatus] = None,
    triggered_by_user_id: Optional[int] = None
) -> List[Type[models.KGPipelineRun]]:
    query = db.query(models.KGPipelineRun)
    if pipeline_id is not None:
        query = query.filter(models.KGPipelineRun.pipeline_id == pipeline_id)
    if status is not None:
        query = query.filter(models.KGPipelineRun.status == status)
    if triggered_by_user_id is not None:
        query = query.filter(models.KGPipelineRun.triggered_by_user_id == triggered_by_user_id)
    
    return query.order_by(models.KGPipelineRun.created_at.desc()).offset(skip).limit(limit).all()

def create_kg_pipeline_run(
    db: Session, run_create: schemas.KGPipelineRunCreate
) -> models.KGPipelineRun:
    db_run = models.KGPipelineRun(
        **run_create.dict(),
        status=schemas.KGPipelineRunStatus.PENDING, # Initial status
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        start_time=datetime.utcnow() # Mark start time immediately on creation for PENDING
    )
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run

def update_kg_pipeline_run_status(
    db: Session, 
    run_id: int, 
    new_status: schemas.KGPipelineRunStatus,
    end_time: Optional[datetime] = None 
) -> Optional[models.KGPipelineRun]:
    db_run = get_kg_pipeline_run(db, run_id=run_id)
    if not db_run:
        return None
    
    db_run.status = new_status
    db_run.updated_at = datetime.utcnow()
    if new_status in [schemas.KGPipelineRunStatus.SUCCESS, schemas.KGPipelineRunStatus.FAILED, schemas.KGPipelineRunStatus.CANCELLED]:
        db_run.end_time = end_time if end_time else datetime.utcnow()
        
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run

# We might add more specific update functions later, e.g., to add logs. 