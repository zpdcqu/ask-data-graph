from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class KGNodeProperty(BaseModel):
    key: str
    value: Any

class KGNode(BaseModel):
    id: str  # Vertex ID
    label: Optional[str] = None # Display label, could be a specific property
    tag: Optional[str] = None # Primary tag of the node
    properties: Optional[Dict[str, Any]] = {}
    # G6 specific styling can be added here too if needed, or handled frontend
    # style: Optional[Dict[str, Any]] = None
    # size: Optional[int] = None 

class KGEdge(BaseModel):
    id: Optional[str] = None # Edge unique ID (e.g., src_vid_edge_type_rank_dst_vid)
    source: str # Source Vertex ID
    target: str # Target Vertex ID
    label: Optional[str] = None # Edge type
    properties: Optional[Dict[str, Any]] = {}
    # G6 specific styling
    # style: Optional[Dict[str, Any]] = None

class KGGraphData(BaseModel):
    nodes: List[KGNode]
    edges: List[KGEdge]
    metadata: Optional[Dict[str, Any]] = None # For any additional info, like query time, total counts etc.

class KGSearchRequest(BaseModel):
    query_string: str
    limit: int = 25
    target_tags: Optional[List[str]] = None # Filter by node tags

class KGNeighborRequest(BaseModel):
    node_id: str
    hops: int = 1
    edge_direction: str = "BOTH" # OUT, IN, BOTH
    limit_per_hop: int = 25 # Limit neighbors at each hop
    target_edge_types: Optional[List[str]] = None 