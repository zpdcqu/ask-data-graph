import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import text as sqlalchemy_text # For raw SQL
from app.db.session import SessionLocal, engine as main_app_engine # To create new sessions
from typing import Any, Optional # Import Any and Optional
from datetime import date, datetime, timezone # For date/datetime conversions

from app.crud import crud_kg_pipeline, crud_kg_pipeline_task, crud_kg_pipeline_run, crud_data_source
from app.api.v1.schemas import kg_pipeline_schemas, kg_pipeline_task_schemas, data_source_schemas as ds_schemas
from app.db.nebula_connector import get_nebula_session
from app.core.config import settings

# Helper to get a SQLAlchemy engine for a given DataSource
# This is a simplified version; production might need more robust engine caching/management
def get_dynamic_engine(ds: ds_schemas.DataSource):
    if ds.type == ds_schemas.DataSourceType.MYSQL:
        # Construct connection URL from ds.connection_params
        # Ensure params like user, password, host, port, database exist
        conn_params = ds.connection_params
        db_url = (
            f"mysql+mysqlclient://{conn_params.get('user')}:{conn_params.get('password')}"
            f"@{conn_params.get('host')}:{conn_params.get('port', 3306)}"
            f"/{conn_params.get('database')}"
        )
        return main_app_engine.execution_options().create_engine(db_url) # Use main engine options for consistency
    # TODO: Add handlers for other DB types (PostgreSQL, etc.)
    raise NotImplementedError(f"Data source type {ds.type} not supported for dynamic engine yet.")

def format_nebula_value(value: Any, target_nebula_type: Optional[str] = None) -> str:
    """Formats a Python value for nGQL, considering the target Nebula data type."""
    if value is None:
        return "NULL"

    if target_nebula_type:
        if target_nebula_type == "STRING":
            # 修复反斜杠语法错误，拆分为多个部分
            escaped_str = str(value).replace('\\', '\\\\').replace('"', '\\"')
            return f"\"{escaped_str}\""
        elif target_nebula_type in ["INT", "INT8", "INT16", "INT32", "INT64"]:
            try:
                return str(int(value))
            except (ValueError, TypeError):
                # print(f"Warning: Could not convert '{value}' to int for type {target_nebula_type}. Returning NULL.")
                return "NULL" # Or raise error, or attempt string conversion
        elif target_nebula_type in ["FLOAT", "DOUBLE"]:
            try:
                return str(float(value))
            except (ValueError, TypeError):
                # print(f"Warning: Could not convert '{value}' to float for type {target_nebula_type}. Returning NULL.")
                return "NULL"
        elif target_nebula_type == "BOOL":
            if isinstance(value, bool):
                return "true" if value else "false"
            # Attempt to infer bool from common string/int representations
            val_lower = str(value).lower()
            if val_lower in ["true", "1", "yes", "t"]:
                return "true"
            elif val_lower in ["false", "0", "no", "f"]:
                return "false"
            # print(f"Warning: Could not convert '{value}' to bool for type {target_nebula_type}. Returning NULL.")
            return "NULL"
        elif target_nebula_type == "DATE":
            # Expects Python date object or ISO format string "YYYY-MM-DD"
            if isinstance(value, date):
                return f"date(\"{value.isoformat()}\")"
            try: # Attempt to parse from string if not already date object
                parsed_date = datetime.strptime(str(value).split(' ')[0], '%Y-%m-%d').date()
                return f"date(\"{parsed_date.isoformat()}\")"
            except ValueError:
                # print(f"Warning: Could not convert '{value}' to DATE. Expected YYYY-MM-DD or date object. Returning NULL.")
                return "NULL"
        elif target_nebula_type == "DATETIME":
            # Expects Python datetime object or ISO format string "YYYY-MM-DDThh:mm:ss.ffffffZ"
            if isinstance(value, datetime):
                # Nebula typically wants UTC. Ensure datetime is timezone-aware or assume UTC.
                dt_utc = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
                return f"datetime(\"{dt_utc.isoformat(timespec='microseconds')}\")"
            try:
                # A more robust parser might be needed here for various datetime string formats
                dt_obj = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
                dt_utc = dt_obj if dt_obj.tzinfo else dt_obj.replace(tzinfo=timezone.utc)
                return f"datetime(\"{dt_utc.isoformat(timespec='microseconds')}\")"
            except ValueError:
                # print(f"Warning: Could not convert '{value}' to DATETIME. Expected ISO format or datetime object. Returning NULL.")
                return "NULL"
        elif target_nebula_type == "TIMESTAMP":
             # Expects an integer (Unix timestamp in seconds)
            try:
                ts = int(value)
                return str(ts) # Nebula timestamps are just integers
            except (ValueError, TypeError):
                # print(f"Warning: Could not convert '{value}' to TIMESTAMP (integer seconds). Returning NULL.")
                return "NULL"
        # Add other types like DURATION, TIME if needed

    # Default/Fallback (if no specific type or type not handled above, treat as string)
    if isinstance(value, str):
        escaped_str = value.replace('\\', '\\\\').replace('"', '\\"')
        return f"\"{escaped_str}\""
    elif isinstance(value, (int, float, bool)):
        return str(value)
    
    # 最后的fallback
    escaped_str = str(value).replace('\\', '\\\\').replace('"', '\\"')
    return f"\"{escaped_str}\"" # Fallback: quote as string

async def execute_pipeline_task(task_id: int, db_pipeline_run_id: int, target_kg_name: str, db: Session):
    task = crud_kg_pipeline_task.get_kg_pipeline_task(db, task_id=task_id)
    if not task or not task.is_enabled:
        print(f"Task {task_id} not found or not enabled. Skipping.")
        return False

    print(f"[Run ID: {db_pipeline_run_id}] Starting Task: {task.task_name} (Order: {task.task_order})")
    
    source_ds_model = crud_data_source.get_data_source(db, task.source_data_source_id)
    if not source_ds_model:
        print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: Source DS {task.source_data_source_id} not found. Failing.")
        return False
    
    # Convert SQLAlchemy model to Pydantic schema for easier dict access if needed
    source_ds = ds_schemas.DataSource.from_orm(source_ds_model)

    extracted_data = []
    # 1. Data Extraction
    if source_ds.type == ds_schemas.DataSourceType.MYSQL:
        try:
            dynamic_engine = get_dynamic_engine(source_ds)
            with dynamic_engine.connect() as connection:
                query = f"SELECT * FROM {task.source_entity_identifier}"
                if task.filter_conditions:
                    query += f" WHERE {task.filter_conditions}"
                query += ";"
                
                print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: Executing query: {query}")
                result = connection.execute(sqlalchemy_text(query))
                extracted_data = [dict(row) for row in result.mappings()] # Fetch as list of dicts
                print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: Extracted {len(extracted_data)} records.")
        except Exception as e:
            print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: MySQL data extraction failed: {e}")
            return False
    else:
        print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: Data source type {source_ds.type} not yet supported for extraction.")
        return False

    if not extracted_data:
        print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: No data extracted. Task considered successful but did nothing.")
        return True

    # 2. Data Transformation and nGQL Generation (simplified)
    # For batching, collect nGQL queries and execute in chunks.
    ngql_queries = []
    print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: Generating nGQL queries...")

    if task.mapping_type == kg_pipeline_task_schemas.KGPipelineTaskMappingType.NODE:
        tag_name = task.target_label_or_type
        vid_col_mapping = task.field_mappings.get("vertex_id_column") # This might be just a string or a dict with type too
        # Assuming vid_col_mapping is just the column name string for now for VID.
        # Nebula Vertex IDs can be string or INT64. If INT64, it should be handled by format_nebula_value.
        vid_col = vid_col_mapping if isinstance(vid_col_mapping, str) else vid_col_mapping.get("name")
        vid_nebula_type = "INT64" if isinstance(vid_col_mapping, dict) and vid_col_mapping.get("type") == "INT64" else "STRING"

        prop_map_config = task.field_mappings.get("properties", {})
        if not vid_col:
            print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: 'vertex_id_column' not in field_mappings. Failing.")
            return False

        for row in extracted_data:
            raw_vid = row.get(vid_col)
            if raw_vid is None:
                continue
            
            formatted_vid = format_nebula_value(raw_vid, vid_nebula_type)
            if formatted_vid == "NULL": # Cannot have NULL Vertex ID
                print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: NULL Vertex ID from column '{vid_col}' for value '{raw_vid}'. Skipping.")
                continue

            props_to_insert = {}
            prop_names_ordered = []
            prop_values_ordered = []
            for src_col, target_mapping in prop_map_config.items():
                if src_col in row:
                    target_prop_name = target_mapping.get("target_property")
                    target_prop_type = target_mapping.get("type") # Nebula type from mapping
                    formatted_val = format_nebula_value(row[src_col], target_prop_type)
                    # Only include non-NULL properties, or handle as per schema requirements
                    if formatted_val != "NULL": 
                        props_to_insert[target_prop_name] = formatted_val 
                        prop_names_ordered.append(f"`{target_prop_name}`")
                        prop_values_ordered.append(formatted_val)
            
            if not prop_names_ordered: # No properties to insert
                ngql = f"INSERT VERTEX `{tag_name}` () VALUES {formatted_vid}:();"
            else:
                prop_names_str = ", ".join(prop_names_ordered)
                prop_values_str = ", ".join(prop_values_ordered)
                ngql = f"INSERT VERTEX `{tag_name}` ({prop_names_str}) VALUES {formatted_vid}:({prop_values_str});"
            ngql_queries.append(ngql)

    elif task.mapping_type == kg_pipeline_task_schemas.KGPipelineTaskMappingType.RELATIONSHIP:
        edge_name = task.target_label_or_type
        # Assume src/dst VID columns also specify their type (STRING or INT64)
        src_vid_col_map = task.field_mappings.get("source_vid_column")
        dst_vid_col_map = task.field_mappings.get("destination_vid_column")
        
        src_vid_col = src_vid_col_map if isinstance(src_vid_col_map, str) else src_vid_col_map.get("name")
        src_vid_type = "INT64" if isinstance(src_vid_col_map, dict) and src_vid_col_map.get("type") == "INT64" else "STRING"
        dst_vid_col = dst_vid_col_map if isinstance(dst_vid_col_map, str) else dst_vid_col_map.get("name")
        dst_vid_type = "INT64" if isinstance(dst_vid_col_map, dict) and dst_vid_col_map.get("type") == "INT64" else "STRING"

        rank_col_map = task.field_mappings.get("rank_column") # rank is always INT64
        rank_col = rank_col_map if isinstance(rank_col_map, str) else rank_col_map.get("name") if rank_col_map else None
        
        prop_map_config = task.field_mappings.get("properties", {})

        if not src_vid_col or not dst_vid_col:
            print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: Missing source/destination VID column. Failing.")
            return False

        for row in extracted_data:
            raw_src_vid = row.get(src_vid_col)
            raw_dst_vid = row.get(dst_vid_col)
            
            if raw_src_vid is None or raw_dst_vid is None:
                continue

            src_vid = format_nebula_value(raw_src_vid, src_vid_type)
            dst_vid = format_nebula_value(raw_dst_vid, dst_vid_type)

            if src_vid == "NULL" or dst_vid == "NULL":
                print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: NULL source or destination Vertex ID after formatting. Skipping.")
                continue

            rank_str = ""
            if rank_col and row.get(rank_col) is not None:
                rank_val = format_nebula_value(row.get(rank_col), "INT64") # Nebula rank is int
                if rank_val != "NULL":
                    rank_str = f"@{rank_val}"

            props_to_insert = {}
            prop_names_ordered = []
            prop_values_ordered = []

            for src_col, target_mapping in prop_map_config.items():
                if src_col in row:
                    target_prop_name = target_mapping.get("target_property")
                    target_prop_type = target_mapping.get("type")
                    formatted_val = format_nebula_value(row[src_col], target_prop_type)
                    if formatted_val != "NULL":
                        props_to_insert[target_prop_name] = formatted_val
                        prop_names_ordered.append(f"`{target_prop_name}`")
                        prop_values_ordered.append(formatted_val)
            
            if not prop_names_ordered:
                ngql = f"INSERT EDGE `{edge_name}` () VALUES {src_vid} -> {dst_vid}{rank_str}:();"
            else:
                prop_names_str = ", ".join(prop_names_ordered)
                prop_values_str = ", ".join(prop_values_ordered)
                ngql = f"INSERT EDGE `{edge_name}` ({prop_names_str}) VALUES {src_vid} -> {dst_vid}{rank_str}:({prop_values_str});"
            ngql_queries.append(ngql)
    else:
        print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: Unsupported mapping type: {task.mapping_type}")
        return False

    # 3. Connect to Nebula Graph and write data (batch execution recommended for large data)
    if ngql_queries:
        print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: Executing {len(ngql_queries)} nGQL queries...")
        # For actual batching, group queries into larger statements or send in chunks
        # E.g., INSERT VERTEX tag1(p1,p2) VALUES "v1":(val1,val2), "v2":(val3,val4);
        # This simplified version executes one by one.
        try:
            with get_nebula_session(space_name=target_kg_name) as nebula_session:
                for i, query in enumerate(ngql_queries):
                    # print(f"Executing nGQL ({i+1}/{len(ngql_queries)}): {query}") # Can be too verbose
                    resp = nebula_session.execute(query)
                    if not resp.is_succeeded():
                        print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: nGQL query failed: {query}. Error: {resp.error_msg()}")
                        # Decide if one failed query should fail the whole task
                        # For now, let's assume it does.
                        return False 
                print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: Successfully executed {len(ngql_queries)} nGQL queries.")
        except Exception as e:
            print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: Nebula Graph operation failed: {e}")
            return False
    else:
        print(f"[Run ID: {db_pipeline_run_id}] Task {task.task_name}: No nGQL queries generated.")

    print(f"[Run ID: {db_pipeline_run_id}] Finished Task: {task.task_name} successfully.")
    return True

async def run_kg_pipeline_background(pipeline_id: int, db_pipeline_run_id: int):
    """Background task to execute a KG pipeline."""
    db: Session = SessionLocal()
    try:
        print(f"Background task started for Pipeline ID: {pipeline_id}, Run ID: {db_pipeline_run_id}")
        crud_kg_pipeline_run.update_kg_pipeline_run_status(
            db, run_id=db_pipeline_run_id, new_status=kg_pipeline_schemas.KGPipelineRunStatus.RUNNING
        )
        pipeline = crud_kg_pipeline.get_kg_pipeline(db, pipeline_id=pipeline_id)
        if not pipeline:
            print(f"Pipeline {pipeline_id} not found. Failing run {db_pipeline_run_id}.")
            crud_kg_pipeline_run.update_kg_pipeline_run_status(
                db, run_id=db_pipeline_run_id, new_status=kg_pipeline_schemas.KGPipelineRunStatus.FAILED
            )
            return

        tasks = crud_kg_pipeline_task.get_kg_pipeline_tasks_for_pipeline(db, pipeline_id=pipeline_id)
        if not tasks:
            print(f"No tasks found for pipeline {pipeline_id}. Marking run {db_pipeline_run_id} as success (empty pipeline).")
            crud_kg_pipeline_run.update_kg_pipeline_run_status(
                db, run_id=db_pipeline_run_id, new_status=kg_pipeline_schemas.KGPipelineRunStatus.SUCCESS
            )
            return
        
        all_tasks_successful = True
        for task_model in sorted(tasks, key=lambda t: t.task_order):
            current_run_status_obj = crud_kg_pipeline_run.get_kg_pipeline_run(db, run_id=db_pipeline_run_id)
            if current_run_status_obj and current_run_status_obj.status == kg_pipeline_schemas.KGPipelineRunStatus.CANCELLED:
                print(f"Run {db_pipeline_run_id} was cancelled. Stopping task execution.")
                all_tasks_successful = False
                break 
            
            task_successful = await execute_pipeline_task(
                task_id=task_model.id, 
                db_pipeline_run_id=db_pipeline_run_id, 
                target_kg_name=pipeline.target_kg_name,
                db=db
            )
            if not task_successful:
                all_tasks_successful = False
                print(f"Task {task_model.task_name} (ID: {task_model.id}) failed. Aborting pipeline run {db_pipeline_run_id}.")
                break
        
        final_status = kg_pipeline_schemas.KGPipelineRunStatus.SUCCESS if all_tasks_successful else kg_pipeline_schemas.KGPipelineRunStatus.FAILED
        current_run_status_obj = crud_kg_pipeline_run.get_kg_pipeline_run(db, run_id=db_pipeline_run_id)
        if current_run_status_obj and current_run_status_obj.status == kg_pipeline_schemas.KGPipelineRunStatus.CANCELLED:
            final_status = kg_pipeline_schemas.KGPipelineRunStatus.CANCELLED
            
        crud_kg_pipeline_run.update_kg_pipeline_run_status(
            db, run_id=db_pipeline_run_id, new_status=final_status
        )
        print(f"Pipeline run {db_pipeline_run_id} finished with status: {final_status}")

    except Exception as e:
        print(f"Error during pipeline run {db_pipeline_run_id}: {e}")
        try:
            crud_kg_pipeline_run.update_kg_pipeline_run_status(
                db, run_id=db_pipeline_run_id, new_status=kg_pipeline_schemas.KGPipelineRunStatus.FAILED
            )
        except Exception as db_err:
            print(f"Failed to update run status to FAILED for run {db_pipeline_run_id} after error: {db_err}")
    finally:
        db.close() 