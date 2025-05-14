from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime # Import datetime

from app.api.v1.schemas import kg_pipeline_schemas as schemas
from app.crud import crud_kg_pipeline, crud_kg_pipeline_run
from app.db.session import get_db
from app.core.deps import get_current_active_user
from app.db.models import user_models # For type hinting
from app.services.kg_pipeline_execution_service import run_kg_pipeline_background # Import the service

router = APIRouter()

@router.post("/", response_model=schemas.KGPipeline, status_code=status.HTTP_201_CREATED)
async def create_kg_pipeline(
    pipeline_in: schemas.KGPipelineCreate,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "editor"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to create pipelines")
    return crud_kg_pipeline.create_kg_pipeline(db=db, pipeline=pipeline_in, user_id=current_user.id)

@router.get("/", response_model=List[schemas.KGPipeline])
async def read_kg_pipelines(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = Query(default=20, le=100),
    is_active: Optional[bool] = Query(None), # As per api_doc.md (status field in model)
    current_user: user_models.User = Depends(get_current_active_user)
):
    # Admins see all, others (editors) see their own by default - adjust as needed
    user_id_filter = None
    if current_user.role not in ["admin"]:
        # According to api_doc.md, POST/GET/PUT/DELETE implies editor/admin can manage.
        # Listing might be open for viewing by more roles or filtered.
        # For now, let's assume non-admins don't see all unless explicitly for their items.
        # This might need refinement based on exact GET permission in api_doc.md
        pass # No specific user filter for general list, or apply one if needed
        
    pipelines = crud_kg_pipeline.get_kg_pipelines(db, skip=skip, limit=limit) # user_id=user_id_filter)
    
    # Further filtering if `is_active` is provided (maps to KGPipelineStatus.ACTIVE/INACTIVE)
    if is_active is not None:
        if is_active:
            pipelines = [p for p in pipelines if p.status == schemas.KGPipelineStatus.ACTIVE]
        else:
            pipelines = [p for p in pipelines if p.status == schemas.KGPipelineStatus.INACTIVE]
            
    return pipelines

@router.get("/{pipeline_id}", response_model=schemas.KGPipeline)
async def read_kg_pipeline(
    pipeline_id: int,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user)
):
    db_pipeline = crud_kg_pipeline.get_kg_pipeline(db, pipeline_id=pipeline_id)
    if not db_pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KG Pipeline not found")
    # Permission: owner, or admin/editor
    if db_pipeline.created_by_user_id != current_user.id and current_user.role not in ["admin", "editor"]:
        # Check if simple viewing is allowed more broadly
        # For now, restricting to owner/admin/editor as per modification rights in api_doc.md
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return db_pipeline

@router.put("/{pipeline_id}", response_model=schemas.KGPipeline)
async def update_kg_pipeline(
    pipeline_id: int,
    pipeline_in: schemas.KGPipelineUpdate,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user)
):
    db_pipeline = crud_kg_pipeline.get_kg_pipeline(db, pipeline_id=pipeline_id)
    if not db_pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KG Pipeline not found")
    if db_pipeline.created_by_user_id != current_user.id and current_user.role not in ["admin", "editor"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return crud_kg_pipeline.update_kg_pipeline(db=db, db_obj=db_pipeline, obj_in=pipeline_in)

@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kg_pipeline(
    pipeline_id: int,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user)
):
    db_pipeline = crud_kg_pipeline.get_kg_pipeline(db, pipeline_id=pipeline_id)
    if not db_pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KG Pipeline not found")
    if db_pipeline.created_by_user_id != current_user.id and current_user.role not in ["admin", "editor"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    crud_kg_pipeline.delete_kg_pipeline(db=db, pipeline_id=pipeline_id)
    return

@router.post("/{pipeline_id}/run", response_model=schemas.KGPipelineRun, status_code=status.HTTP_202_ACCEPTED)
async def trigger_kg_pipeline_run(
    pipeline_id: int,
    background_tasks: BackgroundTasks, # Inject BackgroundTasks
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user)
):
    db_pipeline = crud_kg_pipeline.get_kg_pipeline(db, pipeline_id=pipeline_id)
    if not db_pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KG Pipeline not found")
    if db_pipeline.status != schemas.KGPipelineStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pipeline is not active, cannot run.")
    
    if db_pipeline.created_by_user_id != current_user.id and current_user.role not in ["admin", "editor"]:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to run this pipeline")

    # Create a KGPipelineRun entry in the database.
    run_create_schema = schemas.KGPipelineRunCreate(pipeline_id=pipeline_id, triggered_by_user_id=current_user.id)
    db_run = crud_kg_pipeline_run.create_kg_pipeline_run(db, run_create=run_create_schema)
    
    # Add the pipeline execution to background tasks
    background_tasks.add_task(run_kg_pipeline_background, pipeline_id=db_pipeline.id, db_pipeline_run_id=db_run.id)
    
    print(f"Queued KGPipelineRun record {db_run.id} for pipeline {pipeline_id} by user {current_user.username}. Status: {db_run.status}")
    
    return db_run 