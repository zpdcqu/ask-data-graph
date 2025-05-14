from sqlalchemy.orm import Session
import pymysql
import psycopg2
from typing import Dict, List, Any, Tuple

from app.crud import crud_db_metadata
from app.crud import crud_data_source
from app.api.v1.schemas.db_metadata_schemas import DBSchemaMetadataCreate
from app.api.v1.schemas.data_source_schemas import DataSourceType

class DBMetadataService:
    @staticmethod
    def sync_metadata(db: Session, data_source_id: int) -> Tuple[str, str, int, int]:
        """同步数据源的表结构元数据"""
        # 获取数据源信息
        data_source = crud_data_source.get_data_source(db, data_source_id)
        if not data_source:
            return "数据源不存在", "error", 0, 0
        
        # 根据数据源类型选择相应的同步方法
        if data_source.type == DataSourceType.MYSQL:
            return DBMetadataService._sync_mysql_metadata(db, data_source)
        elif data_source.type == DataSourceType.POSTGRESQL:
            return DBMetadataService._sync_postgresql_metadata(db, data_source)
        else:
            return f"不支持的数据源类型: {data_source.type}", "error", 0, 0
    
    @staticmethod
    def _sync_mysql_metadata(db: Session, data_source) -> Tuple[str, str, int, int]:
        """同步MySQL数据库的表结构元数据"""
        conn_params = data_source.connection_params
        try:
            # 连接MySQL数据库
            connection = pymysql.connect(
                host=conn_params['host'],
                port=int(conn_params.get('port', 3306)),
                user=conn_params['username'],
                password=conn_params['password'],
                database=conn_params['database']
            )
            
            # 先清除现有元数据
            crud_db_metadata.delete_by_data_source(db, data_source.id)
            
            tables_count = 0
            columns_count = 0
            
            with connection.cursor() as cursor:
                # 获取所有表
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                tables_count = len(tables)
                
                for table in tables:
                    table_name = table[0]
                    
                    # 获取表结构
                    cursor.execute(f"DESCRIBE `{table_name}`")
                    columns = cursor.fetchall()
                    
                    # 获取主键信息
                    cursor.execute(f"""
                        SELECT k.COLUMN_NAME
                        FROM information_schema.table_constraints t
                        JOIN information_schema.key_column_usage k
                        USING(constraint_name,table_schema,table_name)
                        WHERE t.constraint_type='PRIMARY KEY'
                        AND t.table_schema=DATABASE()
                        AND t.table_name='{table_name}'
                    """)
                    primary_keys = [row[0] for row in cursor.fetchall()]
                    
                    # 获取外键信息
                    cursor.execute(f"""
                        SELECT
                            k.COLUMN_NAME,
                            k.REFERENCED_TABLE_NAME,
                            k.REFERENCED_COLUMN_NAME
                        FROM information_schema.key_column_usage k
                        JOIN information_schema.table_constraints t
                        USING(constraint_name,table_schema,table_name)
                        WHERE t.constraint_type='FOREIGN KEY'
                        AND t.table_schema=DATABASE()
                        AND t.table_name='{table_name}'
                    """)
                    foreign_keys = {}
                    for fk_row in cursor.fetchall():
                        foreign_keys[fk_row[0]] = {
                            'referenced_table': fk_row[1],
                            'referenced_column': fk_row[2]
                        }
                    
                    # 处理每个列
                    for column in columns:
                        col_name = column[0]
                        data_type = column[1]
                        
                        # 提取列大小
                        col_size = None
                        if '(' in data_type:
                            data_type_parts = data_type.split('(')
                            data_type = data_type_parts[0]
                            col_size = int(data_type_parts[1].split(')')[0])
                        
                        # 获取列的样本值
                        sample_values = []
                        try:
                            cursor.execute(f"SELECT DISTINCT `{col_name}` FROM `{table_name}` LIMIT 5")
                            sample_rows = cursor.fetchall()
                            sample_values = [row[0] for row in sample_rows]
                        except:
                            # 获取样本值失败时忽略错误
                            pass
                        
                        # 创建元数据记录
                        metadata = DBSchemaMetadataCreate(
                            data_source_id=data_source.id,
                            db_name=conn_params['database'],
                            table_name=table_name,
                            column_name=col_name,
                            data_type=data_type,
                            is_primary_key=col_name in primary_keys,
                            is_foreign_key=col_name in foreign_keys,
                            referenced_table=foreign_keys.get(col_name, {}).get('referenced_table'),
                            referenced_column=foreign_keys.get(col_name, {}).get('referenced_column')
                        )
                        
                        # 保存元数据并添加额外信息
                        db_metadata = crud_db_metadata.create_metadata(db, metadata)
                        db_metadata.column_size = col_size
                        db_metadata.sample_values = sample_values
                        db.commit()
                        
                        columns_count += 1
            
            connection.close()
            return "元数据同步成功", "success", tables_count, columns_count
            
        except Exception as e:
            return f"同步MySQL元数据失败: {str(e)}", "error", 0, 0
    
    @staticmethod
    def _sync_postgresql_metadata(db: Session, data_source) -> Tuple[str, str, int, int]:
        """同步PostgreSQL数据库的表结构元数据"""
        conn_params = data_source.connection_params
        try:
            # 连接PostgreSQL数据库
            connection = psycopg2.connect(
                host=conn_params['host'],
                port=int(conn_params.get('port', 5432)),
                user=conn_params['username'],
                password=conn_params['password'],
                dbname=conn_params['database']
            )
            
            # 先清除现有元数据
            crud_db_metadata.delete_by_data_source(db, data_source.id)
            
            tables_count = 0
            columns_count = 0
            
            with connection.cursor() as cursor:
                # 获取所有表
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = cursor.fetchall()
                tables_count = len(tables)
                
                for table in tables:
                    table_name = table[0]
                    
                    # 获取列信息
                    cursor.execute(f"""
                        SELECT 
                            column_name, 
                            data_type,
                            character_maximum_length
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table_name}'
                    """)
                    columns = cursor.fetchall()
                    
                    # 获取主键信息
                    cursor.execute(f"""
                        SELECT a.attname
                        FROM pg_index i
                        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                        WHERE i.indrelid = '{table_name}'::regclass
                        AND i.indisprimary
                    """)
                    primary_keys = [row[0] for row in cursor.fetchall()]
                    
                    # 获取外键信息
                    cursor.execute(f"""
                        SELECT
                            kcu.column_name,
                            ccu.table_name AS referenced_table,
                            ccu.column_name AS referenced_column
                        FROM information_schema.table_constraints AS tc
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                          AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                          AND ccu.table_schema = tc.table_schema
                        WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = '{table_name}'
                    """)
                    foreign_keys = {}
                    for fk_row in cursor.fetchall():
                        foreign_keys[fk_row[0]] = {
                            'referenced_table': fk_row[1],
                            'referenced_column': fk_row[2]
                        }
                    
                    # 处理每个列
                    for column in columns:
                        col_name = column[0]
                        data_type = column[1]
                        col_size = column[2]
                        
                        # 获取列的样本值
                        sample_values = []
                        try:
                            cursor.execute(f"SELECT DISTINCT \"{col_name}\" FROM \"{table_name}\" LIMIT 5")
                            sample_rows = cursor.fetchall()
                            sample_values = [row[0] for row in sample_rows]
                        except:
                            # 获取样本值失败时忽略错误
                            pass
                        
                        # 创建元数据记录
                        metadata = DBSchemaMetadataCreate(
                            data_source_id=data_source.id,
                            db_name=conn_params['database'],
                            table_name=table_name,
                            column_name=col_name,
                            data_type=data_type,
                            is_primary_key=col_name in primary_keys,
                            is_foreign_key=col_name in foreign_keys,
                            referenced_table=foreign_keys.get(col_name, {}).get('referenced_table'),
                            referenced_column=foreign_keys.get(col_name, {}).get('referenced_column')
                        )
                        
                        # 保存元数据并添加额外信息
                        db_metadata = crud_db_metadata.create_metadata(db, metadata)
                        db_metadata.column_size = col_size
                        db_metadata.sample_values = sample_values
                        db.commit()
                        
                        columns_count += 1
            
            connection.close()
            return "元数据同步成功", "success", tables_count, columns_count
            
        except Exception as e:
            return f"同步PostgreSQL元数据失败: {str(e)}", "error", 0, 0 