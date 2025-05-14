from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional
from app.services import kg_visualization_service
from app.api.v1.schemas import kg_visualization_schemas as schemas
from app.core.config import settings

router = APIRouter()

@router.get(
    "/neighbors/{node_id}", 
    response_model=schemas.KGGraphData,
    summary="Get Node Neighbors",
    description="Retrieve neighbors of a specific node in the knowledge graph up to a certain number of hops."
)
async def get_node_neighbors(
    node_id: str = Path(..., title="Node ID", description="The ID of the node to get neighbors for (can be string or integer represented as string)."),
    hops: int = Query(1, ge=1, le=5, title="Hops", description="Number of hops to traverse."),
    limit_per_node: int = Query(settings.NEBULA_VIS_DEFAULT_NEIGHBOR_LIMIT, ge=5, le=100, title="Limit per Node", description="Approximate limit of neighbors/paths to fetch around the node."),
    target_edge_types: Optional[str] = Query(None, title="Target Edge Types", description="Comma-separated list of edge types to focus on (e.g., 'follow,serve'). If None, all edge types are considered.")
):
    """
    Fetches the neighbors of a given node up to a specified number of hops.
    - **node_id**: The ID of the starting node.
    - **hops**: How many steps away from the node_id to look for neighbors.
    - **limit_per_node**: A guideline for how many nodes/edges to return.
    - **target_edge_types**: Optional filter for specific edge types (comma-separated).
    """
    try:
        edge_types_list = target_edge_types.split(',') if target_edge_types else None
        graph_data = await kg_visualization_service.get_graph_neighbors(
            node_id=node_id,
            hops=hops,
            limit_per_node=limit_per_node, # Changed from limit_per_hop to match service param
            target_edge_types=edge_types_list,
            space_name=settings.NEBULA_SPACE_NAME
        )
        if not graph_data.nodes and not graph_data.edges:
            # Distinguish between an empty result and an error if needed
            # For now, an empty graph is a valid response if the node has no neighbors or doesn't exist
            pass
        return graph_data
    except Exception as e:
        # Log the exception e
        print(f"Error in get_node_neighbors endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching graph neighbors: {str(e)}")

@router.get(
    "/search", 
    response_model=schemas.KGGraphData,
    summary="Search Nodes in Knowledge Graph",
    description="Search for nodes in the knowledge graph based on a query string and optional tags."
)
async def search_nodes(
    query_string: str = Query(..., min_length=1, title="Search Query", description="The string to search for in node properties (e.g., name)."),
    limit: int = Query(25, ge=1, le=100, title="Limit", description="Maximum number of nodes to return."),
    target_tags: Optional[str] = Query(None, title="Target Tags", description="Comma-separated list of node tags to search within (e.g., 'player,team'). If None, search may be broader or follow service-defined behavior.")
):
    """
    Searches for nodes in the knowledge graph.
    - **query_string**: The text to search for.
    - **limit**: Maximum number of results.
    - **target_tags**: Optional filter for specific node tags (comma-separated).
    """
    try:
        tags_list = target_tags.split(',') if target_tags else None
        graph_data = await kg_visualization_service.search_kg_nodes(
            query_string=query_string,
            limit=limit,
            target_tags=tags_list,
            space_name=settings.NEBULA_SPACE_NAME
        )
        return graph_data
    except Exception as e:
        # Log the exception e
        print(f"Error in search_nodes endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while searching for nodes: {str(e)}") 