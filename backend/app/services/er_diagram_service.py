from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from collections import defaultdict

from app.crud import crud_db_metadata, crud_er_diagram
from app.api.v1.schemas.er_diagram_schemas import ERDiagramData, TableNode, TableColumn, RelationshipEdge

class ERDiagramService:
    @staticmethod
    def generate_diagram_data(db: Session, data_source_id: int, diagram_id: Optional[int] = None):
        """生成ER图数据结构"""
        # 获取数据源的所有表元数据
        metadata_list = crud_db_metadata.get_by_data_source(db, data_source_id, 0, 10000)
        
        # 如果没有元数据，返回错误
        if not metadata_list:
            return None, "未找到数据源元数据，请先同步元数据"
        
        # 获取数据源的表关系
        relationships = crud_er_diagram.get_relationships_by_data_source(db, data_source_id)
        
        # 如果没有关系数据，返回警告
        if not relationships:
            return None, "未找到表关系数据，请先分析表关系"
        
        # 获取指定ER图配置（如果有）
        diagram_config = None
        if diagram_id:
            diagram_config = crud_er_diagram.get_diagram(db, diagram_id)
        
        # 按表分组元数据
        tables_metadata = defaultdict(list)
        for meta in metadata_list:
            tables_metadata[meta.table_name].append(meta)
        
        # 构建节点数据
        nodes = []
        for table_name, columns_metadata in tables_metadata.items():
            table_columns = []
            for col_meta in columns_metadata:
                table_columns.append(TableColumn(
                    name=col_meta.column_name,
                    data_type=col_meta.data_type,
                    size=col_meta.column_size,
                    is_primary_key=col_meta.is_primary_key,
                    is_foreign_key=col_meta.is_foreign_key,
                    description=col_meta.column_description
                ))
            
            # 从图配置中获取位置信息（如果有）
            position = None
            if diagram_config and diagram_config.layout_data and table_name in diagram_config.layout_data.get('positions', {}):
                position = diagram_config.layout_data['positions'][table_name]
            
            nodes.append(TableNode(
                id=table_name,
                label=table_name,
                columns=table_columns,
                position=position
            ))
        
        # 构建边数据
        edges = []
        for rel in relationships:
            edge_id = f"{rel.source_table}-{rel.target_table}-{rel.id}"
            
            # 创建关系描述标签
            if rel.relationship_type == "one_to_one":
                label = "1:1"
            elif rel.relationship_type == "one_to_many":
                label = "1:N"
            elif rel.relationship_type == "many_to_many":
                label = "N:M"
            else:
                label = "?"
            
            edges.append(RelationshipEdge(
                id=edge_id,
                source=rel.source_table,
                target=rel.target_table,
                relationship_type=rel.relationship_type,
                source_columns=rel.source_columns,
                target_columns=rel.target_columns,
                label=label
            ))
        
        # 获取图显示设置
        settings = {}
        if diagram_config and diagram_config.display_settings:
            settings = diagram_config.display_settings
        
        # 构建完整的ER图数据
        diagram_data = ERDiagramData(
            nodes=nodes,
            edges=edges,
            settings=settings
        )
        
        return diagram_data, None 