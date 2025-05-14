import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import {
    KGGraphData,
    KGNode,
    KGEdge,
    fetchNeighbors as apiFetchNeighbors,
    searchNodes as apiSearchNodes,
    FetchNeighborsParams,
    SearchNodesParams
} from './kgVisualizationApi';

interface KGVisualizationState {
    nodes: KGNode[];
    edges: KGEdge[];
    currentCentralNodeId?: string | null; // To keep track of the central node for neighbor fetching
    status: 'idle' | 'loading' | 'succeeded' | 'failed';
    error: string | null | undefined;
}

const initialState: KGVisualizationState = {
    nodes: [],
    edges: [],
    currentCentralNodeId: null,
    status: 'idle',
    error: null,
};

// Async thunk for fetching neighbors
export const fetchNeighbors = createAsyncThunk<KGGraphData, FetchNeighborsParams>(
    'kgVisualization/fetchNeighbors',
    async (params, { rejectWithValue }) => {
        try {
            const data = await apiFetchNeighbors(params);
            return data;
        } catch (error: any) {
            return rejectWithValue(error.message || 'Failed to fetch neighbors');
        }
    }
);

// Async thunk for searching nodes
export const searchNodes = createAsyncThunk<KGGraphData, SearchNodesParams>(
    'kgVisualization/searchNodes',
    async (params, { rejectWithValue }) => {
        try {
            const data = await apiSearchNodes(params);
            return data;
        } catch (error: any) {
            return rejectWithValue(error.message || 'Failed to search nodes');
        }
    }
);

const kgVisualizationSlice = createSlice({
    name: 'kgVisualization',
    initialState,
    reducers: {
        clearGraphData: (state) => {
            state.nodes = [];
            state.edges = [];
            state.currentCentralNodeId = null;
            state.status = 'idle';
            state.error = null;
        },
        // Action to update graph data, e.g., when G6 component modifies it locally (if needed)
        // Or to add/remove single nodes/edges dynamically
        // For now, focusing on replacing data from API calls
        setGraphData: (state, action: PayloadAction<KGGraphData>) => {
            state.nodes = action.payload.nodes;
            state.edges = action.payload.edges;
            state.status = 'succeeded'; // Assuming direct set means data is ready
        },
        setCurrentCentralNodeId: (state, action: PayloadAction<string | null>) => {
            state.currentCentralNodeId = action.payload;
        }
    },
    extraReducers: (builder) => {
        builder
            // Fetch Neighbors
            .addCase(fetchNeighbors.pending, (state) => {
                state.status = 'loading';
                state.error = null;
            })
            .addCase(fetchNeighbors.fulfilled, (state, action: PayloadAction<KGGraphData>) => {
                state.status = 'succeeded';
                // Logic to merge or replace nodes and edges
                // For simplicity, let's replace for now, assuming each fetch is a new context
                // A more sophisticated approach might merge data if appropriate
                state.nodes = action.payload.nodes;
                state.edges = action.payload.edges;
                // If the call was for neighbors, the first node ID in params was the central one.
                // This helps in centering the graph view if needed.
                // Note: fetchNeighbors thunk currently doesn't pass original params to fulfilled reducer
                // state.currentCentralNodeId = action.meta.arg.nodeId; // If we need it here
            })
            .addCase(fetchNeighbors.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.payload as string; 
            })
            // Search Nodes
            .addCase(searchNodes.pending, (state) => {
                state.status = 'loading';
                state.error = null;
            })
            .addCase(searchNodes.fulfilled, (state, action: PayloadAction<KGGraphData>) => {
                state.status = 'succeeded';
                state.nodes = action.payload.nodes;
                state.edges = action.payload.edges; // Search might return related edges or just nodes
                state.currentCentralNodeId = null; // Reset central node after a search
            })
            .addCase(searchNodes.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.payload as string;
            });
    },
});

export const { clearGraphData, setGraphData, setCurrentCentralNodeId } = kgVisualizationSlice.actions;

export default kgVisualizationSlice.reducer; 