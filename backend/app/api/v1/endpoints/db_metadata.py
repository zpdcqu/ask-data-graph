from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.crud import crud_db_metadata
from app.db.session import get_db
from app.services.db_metadata_service import DBMetadataService
from app.api.v1.schemas import db_metadata_schemas as schemas

router = APIRouter()

@router.post("/data-sources/{data_source_id}/sync", status_code=status.HTTP_202_ACCEPTED, response_model=schemas.SyncResponse)
def sync_metadata(data_source_id: int, db: Session = Depends(get_db)):
    """
    同步指定数据源的表结构元数据
    """
    message, status_str, tables_count, columns_count = DBMetadataService.sync_metadata(db, data_source_id)
    if status_str == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return schemas.SyncResponse(
        message=message,
        status=status_str,
        tables_count=tables_count,
        columns_count=columns_count
    )

@router.get("/data-sources/{data_source_id}", response_model=List[schemas.DBSchemaMetadata])
def get_metadata(
    data_source_id: int,
    skip: int = 0,
    limit: int = 100,
    table_name: str = None,
    column_name: str = None,
    db: Session = Depends(get_db)
):
    """
    获取指定数据源的表结构元数据
    """
    if table_name:
        return crud_db_metadata.get_columns_by_table(db, data_source_id, table_name)
    else:
        return crud_db_metadata.get_by_data_source(db, data_source_id, skip, limit)

@router.get("/data-sources/{data_source_id}/tables", response_model=List[str])
def get_tables(data_source_id: int, db: Session = Depends(get_db)):
    """
    获取指定数据源的所有表名
    """
    return crud_db_metadata.get_tables_by_data_source(db, data_source_id)

@router.put("/{metadata_id}", response_model=schemas.DBSchemaMetadata)
def update_metadata(
    metadata_id: int,
    metadata_update: schemas.DBSchemaMetadataUpdate,
    db: Session = Depends(get_db)
):
    """
    更新元数据描述或其他信息
    """
    updated_metadata = crud_db_metadata.update_metadata(db, metadata_id, metadata_update)
    if updated_metadata is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="元数据记录不存在"
        )
    return updated_metadata 