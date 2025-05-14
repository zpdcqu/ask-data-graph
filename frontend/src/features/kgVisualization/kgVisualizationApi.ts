import apiClient from '../../services/apiClient';
import { AxiosResponse } from 'axios';

// TypeScript interfaces mirroring backend Pydantic schemas
// Based on backend/app/api/v1/schemas/kg_visualization_schemas.py

export interface KGNodeProperty {
    key: string;
    value: any;
}

export interface KGNode {
    id: string; // Vertex ID
    label?: string | null; // Display label
    tag?: string | null; // Primary tag of the node
    properties?: Record<string, any> | null;
    // G6 specific styling can be added here if needed, or handled by the viewer component
    // style?: Record<string, any> | null;
    // size?: number | null;
}

export interface KGEdge {
    id?: string | null; // Edge unique ID (e.g., src_vid_edge_type_rank_dst_vid)
    source: string; // Source Vertex ID
    target: string; // Target Vertex ID
    label?: string | null; // Edge type
    properties?: Record<string, any> | null;
    // G6 specific styling
    // style?: Record<string, any> | null;
}

export interface KGGraphData {
    nodes: KGNode[];
    edges: KGEdge[];
    metadata?: Record<string, any> | null; // For any additional info
}

// Interface for neighbor fetching parameters
export interface FetchNeighborsParams {
    nodeId: string;
    hops?: number;
    limitPerNode?: number;
    targetEdgeTypes?: string[]; // Will be joined to comma-separated string for API
}

// Interface for search parameters
export interface SearchNodesParams {
    queryString: string;
    limit?: number;
    targetTags?: string[]; // Will be joined to comma-separated string for API
}

const KG_VIS_BASE_URL = '/visualize'; // Matches the router prefix in backend

/**
 * Fetches neighbors of a specific node.
 */
export const fetchNeighbors = async (params: FetchNeighborsParams): Promise<KGGraphData> => {
    const { nodeId, hops, limitPerNode, targetEdgeTypes } = params;
    try {
        const response: AxiosResponse<KGGraphData> = await apiClient.get(
            `${KG_VIS_BASE_URL}/neighbors/${encodeURIComponent(nodeId)}`,
            {
                params: {
                    hops: hops,
                    limit_per_node: limitPerNode, // Matches backend query param name
                    target_edge_types: targetEdgeTypes?.join(',') || undefined,
                },
            }
        );
        return response.data;
    } catch (error) {
        console.error('Error fetching neighbors:', error);
        // It's good practice to throw a more specific error or an error object that can be handled by UI
        throw error; 
    }
};

/**
 * Searches for nodes in the knowledge graph.
 */
export const searchNodes = async (params: SearchNodesParams): Promise<KGGraphData> => {
    const { queryString, limit, targetTags } = params;
    try {
        const response: AxiosResponse<KGGraphData> = await apiClient.get(
            `${KG_VIS_BASE_URL}/search`,
            {
                params: {
                    query_string: queryString, // Matches backend query param name
                    limit: limit,
                    target_tags: targetTags?.join(',') || undefined,
                },
            }
        );
        return response.data;
    } catch (error) {
        console.error('Error searching nodes:', error);
        throw error;
    }
}; 