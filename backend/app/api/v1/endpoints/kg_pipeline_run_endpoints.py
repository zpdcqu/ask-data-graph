from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.v1.schemas import kg_pipeline_schemas as schemas
from app.crud import crud_kg_pipeline_run, crud_kg_pipeline
from app.db.session import get_db
from app.core.deps import get_current_active_user
from app.db.models.user_models import User

router = APIRouter()

@router.get("/", response_model=List[schemas.KGPipelineRun])
def read_kg_pipeline_runs(
    skip: int = 0, 
    limit: int = 100, 
    pipeline_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取KG Pipeline Run列表。
    可以选择按pipeline_id筛选。
    """
    if pipeline_id:
        pipeline = crud_kg_pipeline.get_kg_pipeline(db, pipeline_id=pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pipeline with ID {pipeline_id} not found"
            )
        # 检查权限（简单实现，实际应用可能需要更复杂的权限控制）
        if current_user.role != "admin" and pipeline.created_by_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this pipeline's runs"
            )
        return crud_kg_pipeline_run.get_kg_pipeline_runs_for_pipeline(
            db, pipeline_id=pipeline_id, skip=skip, limit=limit
        )
    
    # 如果没有指定pipeline_id，根据用户权限返回
    if current_user.role == "admin":
        return crud_kg_pipeline_run.get_kg_pipeline_runs(db, skip=skip, limit=limit)
    else:
        # 只返回用户创建的pipeline的runs
        pipelines = crud_kg_pipeline.get_kg_pipelines_by_user(db, user_id=current_user.id)
        pipeline_ids = [p.id for p in pipelines]
        if not pipeline_ids:
            return []
        return crud_kg_pipeline_run.get_kg_pipeline_runs_for_pipelines(
            db, pipeline_ids=pipeline_ids, skip=skip, limit=limit
        )

@router.get("/{run_id}", response_model=schemas.KGPipelineRun)
def read_kg_pipeline_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取单个KG Pipeline Run的详细信息。
    """
    run = crud_kg_pipeline_run.get_kg_pipeline_run(db, run_id=run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline run with ID {run_id} not found"
        )
    
    # 获取关联的pipeline以进行权限检查
    pipeline = crud_kg_pipeline.get_kg_pipeline(db, pipeline_id=run.pipeline_id)
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Associated pipeline not found"
        )
    
    # 权限检查
    if current_user.role != "admin" and pipeline.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this pipeline run"
        )
    
    return run

@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kg_pipeline_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除一个KG Pipeline Run。
    """
    run = crud_kg_pipeline_run.get_kg_pipeline_run(db, run_id=run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline run with ID {run_id} not found"
        )
    
    # 获取关联的pipeline以进行权限检查
    pipeline = crud_kg_pipeline.get_kg_pipeline(db, pipeline_id=run.pipeline_id)
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Associated pipeline not found"
        )
    
    # 权限检查 - 只有admin或pipeline创建者可以删除run
    if current_user.role != "admin" and pipeline.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this pipeline run"
        )
    
    crud_kg_pipeline_run.delete_kg_pipeline_run(db, run_id=run_id)
    return None 