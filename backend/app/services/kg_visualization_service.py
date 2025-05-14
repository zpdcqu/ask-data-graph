from typing import List, Dict, Any, Tuple, Set, Optional
from app.db.nebula_connector import get_nebula_session
from app.api.v1.schemas import kg_visualization_schemas as schemas
from app.core.config import settings # For default space name
from nebula3.data.DataObject import ValueWrapper, Node, Relationship, PathWrapper

def format_nebula_value_for_json(value_wrapper: ValueWrapper) -> Any:
    """Decodes a Nebula ValueWrapper to a basic Python type for JSON serialization."""
    if value_wrapper.is_null():
        return None
    elif value_wrapper.is_empty():
        return ""
    elif value_wrapper.is_bool():
        return value_wrapper.as_bool()
    elif value_wrapper.is_int():
        return value_wrapper.as_int()
    elif value_wrapper.is_double():
        return value_wrapper.as_double()
    elif value_wrapper.is_string():
        return value_wrapper.as_string()
    elif value_wrapper.is_date():
        d = value_wrapper.as_date()
        return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
    elif value_wrapper.is_datetime():
        dt = value_wrapper.as_datetime()
        # Format to ISO 8601 like string
        return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}T{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}.{dt.microsecond:06d}{dt.timezone_offset_str}"
    elif value_wrapper.is_time():
        t = value_wrapper.as_time()
        return f"{t.hour:02d}:{t.minute:02d}:{t.second:02d}.{t.microsecond:06d}"
    elif value_wrapper.is_list():
        return [format_nebula_value_for_json(item) for item in value_wrapper.as_list()]
    elif value_wrapper.is_map():
        return {k: format_nebula_value_for_json(v) for k, v in value_wrapper.as_map().items()}
    elif value_wrapper.is_set():
        # Convert set to list for JSON serialization
        return [format_nebula_value_for_json(item) for item in value_wrapper.as_set()]
    # Path, Vertex, Edge might need specific handling if directly returned in a map/list
    # For now, fallback to string representation if type is complex and not handled above
    return value_wrapper.as_string() 

def parse_nebula_node(node: Node) -> schemas.KGNode:
    props = {}
    node_tags = node.tags()
    primary_tag = "UnknownTag"

    if node_tags:
        primary_tag = node_tags[0] # Use the first tag as the primary tag
        # Ensure properties are accessed using the correct tag name
        raw_props = node.properties(primary_tag)
        if raw_props:
            props = {key: format_nebula_value_for_json(val_wrapper)
                     for key, val_wrapper in raw_props.items()}
    
    # Try to find a common label property, or use VID
    label_prop_candidates = ["name", "label", "title", "id"] # Common properties for labels
    node_id_str = node.get_id().as_string() if node.get_id().is_string() else str(node.get_id().as_int())
    node_label = node_id_str # Default to VID string

    for candidate in label_prop_candidates:
        if candidate in props and props[candidate]:
            node_label = str(props[candidate])
            break
            
    return schemas.KGNode(
        id=node_id_str,
        label=node_label,
        tag=primary_tag,
        properties=props
    )

def parse_nebula_edge(edge: Relationship, edge_id_counter: Dict[str, int]) -> schemas.KGEdge:
    props = {key: format_nebula_value_for_json(val_wrapper)
               for key, val_wrapper in edge.properties().items()}
    
    src_vid_wrapper = edge.get_src_vid()
    dst_vid_wrapper = edge.get_dst_vid()

    src_id = src_vid_wrapper.as_string() if src_vid_wrapper.is_string() else str(src_vid_wrapper.as_int())
    dst_id = dst_vid_wrapper.as_string() if dst_vid_wrapper.is_string() else str(dst_vid_wrapper.as_int())
    
    edge_name = edge.edge_name()
    rank = edge.ranking()

    # Create a unique ID for G6 based on Nebula's edge components: (src_id, edge_name, rank, dst_id)
    # This combination is unique in Nebula for a given edge direction.
    # Adding a counter for G6 in case G6 needs truly globally unique IDs if multiple identical edges were possible in a flat list (unlikely for graph data structure)
    base_edge_key = f"{src_id}_{edge_name}_{rank}_{dst_id}"
    
    # For G6, ensure id is a string and globally unique if displayed flatly
    # Nebula's internal edge representation is unique by (src, type, rank, dst).
    # The `id` for KGEdge schema can be this composite key or a simpler one if context implies uniqueness.
    # Let's use the composite key for clarity and uniqueness.
    unique_edge_id = base_edge_key

    return schemas.KGEdge(
        id=unique_edge_id, # This ID should be unique for G6
        source=src_id,
        target=dst_id,
        label=edge_name, # Edge type name as label
        properties=props
    )

async def get_graph_neighbors(
    node_id: str, 
    hops: int = 1, 
    # edge_direction: str = "BOTH", # Parameter not used in current MATCH query, MATCH is inherently bidirectional unless specified in pattern
    limit_per_node: int = 25, # Controls limit in final query, not strictly "per hop" in this simplified MATCH
    target_edge_types: Optional[List[str]] = None,
    space_name: str = settings.NEBULA_SPACE_NAME
) -> schemas.KGGraphData:
    nodes_map: Dict[str, schemas.KGNode] = {}
    final_edges: List[schemas.KGEdge] = []
    # edge_id_counter is not strictly needed if Nebula's composite edge key is used as ID
    # but parse_nebula_edge was designed with it, let's pass an empty one for now.
    edge_id_counter: Dict[str, int] = {} 


    query_node_id = f'"{node_id}"' if not node_id.isdigit() else node_id

    # Construct MATCH query for paths
    # Example: MATCH p=(v1)-[e*1..2]-(v2) WHERE id(v1) == "player100" RETURN p LIMIT 50
    # Edge type filtering: -[e:follow|:serve*1..2]-
    edge_pattern = "*" # Default: all edge types
    if target_edge_types:
        edge_pattern = ":" + "|:".join([f"`{et}`" for et in target_edge_types])
    
    # The limit here is on the number of paths returned. 
    # Each path can contain multiple nodes and edges.
    # limit_per_node is a loose guide for this overall limit.
    path_limit = limit_per_node * (hops + 5) # Heuristic for path limit

    match_query = (
        f"MATCH p=(v1)-[e*{edge_pattern}*1..{hops}]-(v2) "
        f"WHERE id(v1) == {query_node_id} "
        f"RETURN p LIMIT {path_limit}"
    )
    
    print(f"Executing KG Neighbor Query: {match_query}")

    try:
        with get_nebula_session(space_name=space_name) as session:
            # Using execute_json_query to get structured data if possible,
            # or fallback to execute and parse ResultSet if more control is needed.
            # The structure of execute_json_query for paths needs to be handled carefully.
            # It returns a list of paths, where each path contains nodes and relationships.
            # Example result for a path: {"meta": [...], "row": [{"nodes": [...], "relationships": [...]}]}
            # Let's use execute() and manual parsing for more robust handling of PathWrapper
            
            result_set = session.execute(match_query)
            if not result_set.is_succeeded():
                print(f"Error executing neighbor query: {result_set.error_msg()}")
                return schemas.KGGraphData(nodes=[], edges=[])

            for i in range(result_set.row_size()):
                row_value = result_set.row_values(i)
                if not row_value: continue
                
                path_wrapper = row_value[0] # Path is typically the first (and only) yielded item
                
                if isinstance(path_wrapper, ValueWrapper) and path_wrapper.is_path():
                    path = path_wrapper.as_path()
                    
                    # Process nodes in the path
                    for node_obj in path.nodes():
                        parsed_node = parse_nebula_node(node_obj)
                        if parsed_node.id not in nodes_map:
                            nodes_map[parsed_node.id] = parsed_node
                    
                    # Process relationships in the path
                    for edge_obj in path.relationships():
                        # Ensure edge directionality or uniqueness is handled.
                        # The parse_nebula_edge creates an ID based on src,type,rank,dst
                        parsed_edge = parse_nebula_edge(edge_obj, edge_id_counter)
                        
                        # Check if this specific edge (by its unique Nebula properties) is already added
                        # This avoids duplicate edges if paths overlap.
                        # We need a way to uniquely identify an edge from edge_obj before parsing if final_edges stores parsed_edge
                        # A set of edge_keys (src_type_rank_dst) can track added edges.
                        edge_key = f"{parsed_edge.source}_{parsed_edge.label}_{edge_obj.ranking()}_{parsed_edge.target}"
                        
                        is_new_edge = True
                        for fe in final_edges:
                            if fe.id == parsed_edge.id : # parsed_edge.id is already unique key
                                is_new_edge = False
                                break
                        if is_new_edge:
                            final_edges.append(parsed_edge)

                            # Ensure source and target nodes of this edge are in nodes_map (should be, as they are from path)
                            if parsed_edge.source not in nodes_map and path.start_node().get_id().as_string() != parsed_edge.source:
                                # This might happen for edges where one node is outside the immediate path segments but connected.
                                # For simplicity, current parsing relies on path.nodes().
                                print(f"Warning: Source node {parsed_edge.source} of edge {parsed_edge.id} not found in path nodes.")
                            if parsed_edge.target not in nodes_map:
                                print(f"Warning: Target node {parsed_edge.target} of edge {parsed_edge.id} not found in path nodes.")
                else:
                    print(f"Warning: Expected PathWrapper, got {type(path_wrapper)} for row item.")
    
    except Exception as e:
        print(f"Exception in get_graph_neighbors: {e}")
        # Optionally re-raise or return empty graph on critical error
        return schemas.KGGraphData(nodes=[], edges=[])

    return schemas.KGGraphData(nodes=list(nodes_map.values()), edges=final_edges)

async def search_kg_nodes(
    query_string: str, 
    limit: int = 25, 
    target_tags: Optional[List[str]] = None, # If None, search might be broader or require specific index setup
    space_name: str = settings.NEBULA_SPACE_NAME
) -> schemas.KGGraphData:
    nodes_map: Dict[str, schemas.KGNode] = {}
    
    # This is a basic search. NebulaGraph's Full-Text Search is recommended for production.
    # This example assumes searching a common property like 'name' using CONTAINS.
    # Requires index on that property for reasonable performance, e.g., CREATE TAG INDEX IF NOT EXISTS name_idx ON player(name(256));

    # If no target_tags, searching all tags is inefficient.
    # For this example, if target_tags is None, we won't proceed with a generic query.
    # A real application might default to a list of common tags or use full-text search.
    if not target_tags:
        print("Warning: No target tags specified for search. Full-text search or specific tags are recommended.")
        # Attempt a very generic match if no tags, this will be slow without global indexes.
        # For this example, let's assume a common property 'name' might exist on various tags.
        # This is a simplified fallback and not ideal.
        search_gql = f'MATCH (v) WHERE v.name CONTAINS "{query_string}" RETURN v LIMIT {limit}'
        # An alternative using LOOKUP if a global index on 'name' existed (less common for LOOKUP)
        # search_gql = f'LOOKUP ON * WHERE tagName.name CONTAINS "{query_string}" ...' (pseudo-code for all tags)
    else:
        # Construct queries for each target tag
        # MATCH (v:`Player`) WHERE v.Player.name CONTAINS "keyword" RETURN v
        # Or LOOKUP ON `Player` WHERE `Player`.name CONTAINS "keyword" YIELD id(vertex)
        # For simplicity, let's use MATCH for broader compatibility if exact index names are unknown.
        match_clauses = []
        for tag in target_tags:
            # Assuming 'name' property exists on the tag. This should be configurable.
            # Escaping tag name just in case it has special characters, though unlikely for typical tags.
            safe_tag = f"`{tag}`"
            match_clauses.append(f"MATCH (v:{safe_tag}) WHERE v.{safe_tag}.name CONTAINS \"{query_string}\" RETURN v")
        
        # Union all match queries if multiple tags
        # Note: Nebula doesn't support UNION ALL in quite the same way as SQL for arbitrary queries.
        # We'll execute them sequentially and merge results, or use a single complex query if possible.
        # For now, execute one by one if multiple tags, and aggregate.
        # A simpler approach for multiple tags with one property:
        # MATCH (v) WHERE (v:Tag1 AND v.Tag1.name CONTAINS "...") OR (v:Tag2 AND v.Tag2.name CONTAINS "...") RETURN v
        # This requires knowing all tags in advance for the WHERE clause.

        # Let's make one query if possible, or loop.
        # For simplicity, we'll just use the first tag if multiple are given, or require user to specify one.
        # A robust solution would iterate or build a more complex query.
        if target_tags: # Ensure list is not empty
            primary_tag = f"`{target_tags[0]}`" # Use first tag for simplicity
            # Property name 'name' is assumed. This should be a parameter or part of schema.
            search_gql = f'MATCH (v:{primary_tag}) WHERE v.name CONTAINS "{query_string}" RETURN v LIMIT {limit}'
            if len(target_tags) > 1:
                print(f"Warning: Searching only on the first tag provided: {target_tags[0]}. Multiple tag search needs more complex query.")
        else: # Should have been caught by the initial `if not target_tags:`
             return schemas.KGGraphData(nodes=[], edges=[])


    print(f"Executing KG Node Search Query: {search_gql}")
    
    try:
        with get_nebula_session(space_name=space_name) as session:
            result_set = session.execute(search_gql)

            if not result_set.is_succeeded():
                print(f"Error executing search query: {result_set.error_msg()}")
                return schemas.KGGraphData(nodes=[], edges=[])

            for i in range(result_set.row_size()):
                row_value = result_set.row_values(i)
                if not row_value: continue
                
                vertex_wrapper = row_value[0] # Expecting a vertex in the result
                if isinstance(vertex_wrapper, ValueWrapper) and vertex_wrapper.is_vertex():
                    node_obj = vertex_wrapper.as_node()
                    parsed_node = parse_nebula_node(node_obj)
                    if parsed_node.id not in nodes_map:
                        nodes_map[parsed_node.id] = parsed_node
                else:
                    print(f"Warning: Expected Vertex in search result, got {type(vertex_wrapper)}")
    
    except Exception as e:
        print(f"Exception in search_kg_nodes: {e}")
        return schemas.KGGraphData(nodes=[], edges=[])

    return schemas.KGGraphData(nodes=list(nodes_map.values()), edges=[]) # Search typically returns nodes; edges are context-dependent 