from sqlalchemy.orm import Session
from typing import Dict, List, Any, Tuple, Set
import re
from collections import defaultdict

from app.crud import crud_db_metadata, crud_er_diagram
from app.db.models.db_metadata_models import DBSchemaMetadata
from app.api.v1.schemas.er_diagram_schemas import RelationshipType, TableRelationshipCreate, IdentificationMethod

class ERRelationshipService:
    @staticmethod
    def analyze_relationships(db: Session, data_source_id: int):
        """分析数据源的表关系并保存到数据库"""
        # 获取数据源的所有表元数据
        metadata_list = crud_db_metadata.get_by_data_source(db, data_source_id, 0, 10000)
        
        # 如果没有元数据，返回错误
        if not metadata_list:
            return "未找到数据源元数据，请先同步元数据", "error", 0
        
        # 清除旧的关系数据
        crud_er_diagram.delete_relationships_by_data_source(db, data_source_id)
        
        # 按表分组元数据
        tables_metadata = defaultdict(list)
        for meta in metadata_list:
            tables_metadata[meta.table_name].append(meta)
        
        # 识别表关系
        relationships = []
        
        # 识别外键定义的关系
        fk_relationships = ERRelationshipService._identify_fk_relationships(tables_metadata)
        relationships.extend(fk_relationships)
        
        # 识别命名约定暗示的关系
        naming_relationships = ERRelationshipService._identify_naming_relationships(tables_metadata)
        # 过滤掉已经通过外键识别的关系
        for rel in naming_relationships:
            if not any(r['source_table'] == rel['source_table'] and 
                      r['target_table'] == rel['target_table'] and
                      set(r['source_columns']) == set(rel['source_columns']) for r in fk_relationships):
                relationships.append(rel)
        
        # 保存关系到数据库
        created_count = 0
        for rel_data in relationships:
            relationship = TableRelationshipCreate(
                data_source_id=data_source_id,
                source_table=rel_data['source_table'],
                target_table=rel_data['target_table'],
                relationship_type=rel_data['relationship_type'],
                source_columns=rel_data['source_columns'],
                target_columns=rel_data['target_columns'],
                is_identified=rel_data['is_identified'],
                confidence_score=rel_data['confidence_score'],
                description=rel_data['description']
            )
            crud_er_diagram.create_relationship(db, relationship)
            created_count += 1
        
        return f"成功识别 {created_count} 个表关系", "success", created_count
    
    @staticmethod
    def _identify_fk_relationships(tables_metadata):
        """基于外键定义识别表关系"""
        relationships = []
        
        # 收集所有表的主键信息
        pk_info = {}
        for table_name, columns in tables_metadata.items():
            pk_columns = [col.column_name for col in columns if col.is_primary_key]
            if pk_columns:
                pk_info[table_name] = pk_columns
        
        # 识别外键关系
        for table_name, columns in tables_metadata.items():
            for column in columns:
                if column.is_foreign_key and column.referenced_table and column.referenced_column:
                    target_table = column.referenced_table
                    target_column = column.referenced_column
                    source_column = column.column_name
                    
                    # 判断关系类型
                    relationship_type = RelationshipType.ONE_TO_MANY
                    
                    # 如果引用列是目标表的主键并且本表的这列也是主键，可能是一对一关系
                    if target_column in pk_info.get(target_table, []) and source_column in pk_info.get(table_name, []):
                        relationship_type = RelationshipType.ONE_TO_ONE
                    
                    # 多对多通常需要中间表，这里简单判断：如果表有两个或以上外键且都是主键，可能是多对多关系的中间表
                    fk_pk_count = sum(1 for col in columns if col.is_foreign_key and col.is_primary_key)
                    if fk_pk_count >= 2:
                        relationship_type = RelationshipType.MANY_TO_MANY
                    
                    relationships.append({
                        'source_table': table_name,
                        'target_table': target_table,
                        'source_columns': [source_column],
                        'target_columns': [target_column],
                        'relationship_type': relationship_type,
                        'is_identified': IdentificationMethod.AUTO,
                        'confidence_score': 100,  # 外键定义的关系置信度最高
                        'description': f"基于外键约束识别: {table_name}.{source_column} -> {target_table}.{target_column}"
                    })
        
        return relationships
    
    @staticmethod
    def _identify_naming_relationships(tables_metadata):
        """基于命名约定识别可能的表关系"""
        relationships = []
        
        # 识别命名相似的ID列
        for source_table, source_columns in tables_metadata.items():
            for target_table, target_columns in tables_metadata.items():
                if source_table == target_table:
                    continue
                
                source_pk = [col.column_name for col in source_columns if col.is_primary_key]
                if not source_pk:
                    continue
                
                # 查找目标表中与源表名+id命名类似的列
                source_table_singular = ERRelationshipService._get_singular_form(source_table)
                pattern = f"{source_table_singular}_id|{source_table}_id|{source_table}id"
                
                for target_col in target_columns:
                    if re.match(pattern, target_col.column_name, re.IGNORECASE) and not target_col.is_foreign_key:
                        # 找到了可能的关系
                        relationship_type = RelationshipType.ONE_TO_MANY
                        
                        # 如果这个列是目标表的主键，可能是一对一关系
                        if target_col.is_primary_key:
                            relationship_type = RelationshipType.ONE_TO_ONE
                        
                        relationships.append({
                            'source_table': source_table,
                            'target_table': target_table,
                            'source_columns': source_pk,
                            'target_columns': [target_col.column_name],
                            'relationship_type': relationship_type,
                            'is_identified': IdentificationMethod.AUTO,
                            'confidence_score': 70,  # 命名约定的关系置信度较低
                            'description': f"基于命名约定推断: {target_table}.{target_col.column_name} 可能引用 {source_table}.{source_pk[0]}"
                        })
        
        return relationships
    
    @staticmethod
    def _get_singular_form(table_name):
        """简单的获取表名单数形式方法"""
        if table_name.endswith('ies'):
            return table_name[:-3] + 'y'
        elif table_name.endswith('s'):
            return table_name[:-1]
        return table_name 