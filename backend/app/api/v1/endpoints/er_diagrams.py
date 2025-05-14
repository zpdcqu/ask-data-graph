from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.db.session import get_db
from app.services.er_relationship_service import ERRelationshipService
from app.services.er_diagram_service import ERDiagramService
from app.crud import crud_er_diagram
from app.api.v1.schemas import er_diagram_schemas as schemas

router = APIRouter()

@router.post("/data-sources/{data_source_id}/analyze-relationships", status_code=status.HTTP_202_ACCEPTED, response_model=schemas.SyncResponse)
def analyze_relationships(data_source_id: int, db: Session = Depends(get_db)):
    """
    分析指定数据源的表关系
    """
    message, status_str, count = ERRelationshipService.analyze_relationships(db, data_source_id)
    if status_str == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"message": message, "status": status_str, "count": count}

@router.get("/data-sources/{data_source_id}/relationships", response_model=List[schemas.TableRelationship])
def get_relationships(
    data_source_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取指定数据源的表关系列表
    """
    return crud_er_diagram.get_relationships_by_data_source(db, data_source_id, skip, limit)

@router.get("/relationships/{relationship_id}", response_model=schemas.TableRelationship)
def get_relationship(
    relationship_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定ID的表关系详情
    """
    relationship = crud_er_diagram.get_relationship(db, relationship_id)
    if relationship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="表关系不存在"
        )
    return relationship

@router.put("/relationships/{relationship_id}", response_model=schemas.TableRelationship)
def update_relationship(
    relationship_id: int,
    relationship_update: schemas.TableRelationshipUpdate,
    db: Session = Depends(get_db)
):
    """
    更新表关系
    """
    updated_relationship = crud_er_diagram.update_relationship(db, relationship_id, relationship_update)
    if updated_relationship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="表关系不存在"
        )
    return updated_relationship

@router.post("/data-sources/{data_source_id}/diagrams", response_model=schemas.ERDiagram, status_code=status.HTTP_201_CREATED)
def create_diagram(
    data_source_id: int,
    diagram_create: schemas.ERDiagramCreate,
    db: Session = Depends(get_db)
):
    """
    为指定数据源创建ER图配置
    """
    # 确保data_source_id一致
    if diagram_create.data_source_id != data_source_id:
        diagram_create.data_source_id = data_source_id
    
    return crud_er_diagram.create_diagram(db, diagram_create)

@router.get("/data-sources/{data_source_id}/diagrams", response_model=List[schemas.ERDiagram])
def get_diagrams(
    data_source_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取指定数据源的ER图配置列表
    """
    return crud_er_diagram.get_diagrams_by_data_source(db, data_source_id, skip, limit)

@router.get("/diagrams/{diagram_id}", response_model=schemas.ERDiagram)
def get_diagram(
    diagram_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定ID的ER图配置详情
    """
    diagram = crud_er_diagram.get_diagram(db, diagram_id)
    if diagram is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ER图配置不存在"
        )
    return diagram

@router.put("/diagrams/{diagram_id}", response_model=schemas.ERDiagram)
def update_diagram(
    diagram_id: int,
    diagram_update: schemas.ERDiagramUpdate,
    db: Session = Depends(get_db)
):
    """
    更新ER图配置
    """
    updated_diagram = crud_er_diagram.update_diagram(db, diagram_id, diagram_update)
    if updated_diagram is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ER图配置不存在"
        )
    return updated_diagram

@router.delete("/diagrams/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diagram(
    diagram_id: int,
    db: Session = Depends(get_db)
):
    """
    删除ER图配置
    """
    success = crud_er_diagram.delete_diagram(db, diagram_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ER图配置不存在"
        )
    return None

@router.get("/data-sources/{data_source_id}/diagram-data", response_model=schemas.ERDiagramData)
def get_diagram_data(
    data_source_id: int,
    diagram_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    获取指定数据源的ER图数据
    """
    diagram_data, error_message = ERDiagramService.generate_diagram_data(db, data_source_id, diagram_id)
    if diagram_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    return diagram_data 