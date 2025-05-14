from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.v1.schemas import kg_pipeline_task_schemas as schemas
from app.crud import crud_kg_pipeline_task, crud_kg_pipeline
from app.db.session import get_db
from app.core.deps import get_current_active_user
from app.db.models import user_models # For type hinting

router = APIRouter()

@router.post("/", response_model=schemas.KGPipelineTask, status_code=status.HTTP_201_CREATED)
async def create_kg_pipeline_task(
    pipeline_id: int, # Path parameter from the parent router
    task_in: schemas.KGPipelineTaskCreate,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user)
):
    if task_in.pipeline_id != pipeline_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pipeline ID in path and body mismatch")

    pipeline = crud_kg_pipeline.get_kg_pipeline(db, pipeline_id=pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent KG Pipeline not found")
    
    # Permission check: User must be owner of pipeline or admin/editor
    if pipeline.created_by_user_id != current_user.id and current_user.role not in ["admin", "editor"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions for this pipeline")

    created_task = crud_kg_pipeline_task.create_kg_pipeline_task(db=db, task=task_in)
    if not created_task: # Should not happen if pipeline check passed, but for safety
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create task")
    return created_task

@router.get("/", response_model=List[schemas.KGPipelineTask])
async def read_kg_pipeline_tasks(
    pipeline_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    current_user: user_models.User = Depends(get_current_active_user) # For permission check on pipeline
):
    pipeline = crud_kg_pipeline.get_kg_pipeline(db, pipeline_id=pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent KG Pipeline not found")
    
    # Permission to view tasks: if user can view pipeline
    if pipeline.created_by_user_id != current_user.id and current_user.role not in ["admin", "editor"]:
         # Potentially allow broader read access based on requirements
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to view tasks for this pipeline")

    return crud_kg_pipeline_task.get_kg_pipeline_tasks_for_pipeline(
        db, pipeline_id=pipeline_id, skip=skip, limit=limit
    )

@router.get("/{task_id}", response_model=schemas.KGPipelineTask)
async def read_kg_pipeline_task(
    pipeline_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user)
):
    task = crud_kg_pipeline_task.get_kg_pipeline_task(db, task_id=task_id)
    if not task or task.pipeline_id != pipeline_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KG Pipeline Task not found or not part of specified pipeline")
    
    pipeline = crud_kg_pipeline.get_kg_pipeline(db, pipeline_id=pipeline_id)
    # Redundant check for pipeline existence if task found, but good for permission
    if not pipeline or (pipeline.created_by_user_id != current_user.id and current_user.role not in ["admin", "editor"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        
    return task

@router.put("/{task_id}", response_model=schemas.KGPipelineTask)
async def update_kg_pipeline_task(
    pipeline_id: int,
    task_id: int,
    task_in: schemas.KGPipelineTaskUpdate,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user)
):
    db_task = crud_kg_pipeline_task.get_kg_pipeline_task(db, task_id=task_id)
    if not db_task or db_task.pipeline_id != pipeline_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KG Pipeline Task not found")

    pipeline = crud_kg_pipeline.get_kg_pipeline(db, pipeline_id=db_task.pipeline_id)
    if not pipeline or (pipeline.created_by_user_id != current_user.id and current_user.role not in ["admin", "editor"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return crud_kg_pipeline_task.update_kg_pipeline_task(db=db, db_obj=db_task, obj_in=task_in)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kg_pipeline_task(
    pipeline_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user)
):
    db_task = crud_kg_pipeline_task.get_kg_pipeline_task(db, task_id=task_id)
    if not db_task or db_task.pipeline_id != pipeline_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KG Pipeline Task not found")

    pipeline = crud_kg_pipeline.get_kg_pipeline(db, pipeline_id=db_task.pipeline_id)
    if not pipeline or (pipeline.created_by_user_id != current_user.id and current_user.role not in ["admin", "editor"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    crud_kg_pipeline_task.delete_kg_pipeline_task(db=db, task_id=task_id)
    return 