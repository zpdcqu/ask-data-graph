import React, { useEffect, useRef, useMemo } from 'react';
// Importing G6 v5 main class and some core types. Specific types might need further refinement.
import { Graph } from '@antv/g6';
import type { GraphData, NodeModelConfig, EdgeModelConfig, IGraphEvent, GraphOptions } from '@antv/g6';

import { KGNode, KGEdge } from '../../features/kgVisualization/kgVisualizationApi';

// Helper function to create a simple arrow path
const getTriangleArrowPath = (width: number, height: number, offset: number) => {
    return [
        ['M', offset, 0],
        ['L', width + offset, height / 2],
        ['L', offset, height],
        ['Z'], // Close the path
    ];
};

const mapToG6Data = (nodes: KGNode[], edges: KGEdge[]): GraphData => {
    const g6Nodes: NodeModelConfig[] = nodes.map(node => ({
        id: node.id,
        label: node.label || node.id,
        style: {
            fill: node.tag === 'Person' ? '#C6E5FF' : (node.tag === 'Organization' ? '#D5FFD6' : '#FFD8B8'),
            stroke: node.tag === 'Person' ? '#5B8FF9' : (node.tag === 'Organization' ? '#5AD85A' : '#F6BD16'),
            lineWidth: 1,
        },
        originalData: node 
    }));

    const g6Edges: EdgeModelConfig[] = edges.map(edge => ({
        id: edge.id || `${edge.source}-${edge.label}-${edge.target}-${Math.random().toString(36).substr(2, 9)}`,
        source: edge.source,
        target: edge.target,
        label: edge.label || '',
        style: {
            stroke: '#999',
            lineWidth: 1.5,
            endArrow: {
                // path: getTriangleArrowPath(10, 12, 0), // Using custom path function
                // Or using G6 v5 built-in marker types if available and preferred:
                // type: 'triangle', // e.g. if G6 supports this string directly for default markers
                // size: [10,12] // or similar config
                // For simplicity, let's use a boolean and let G6 default arrow if simple enough or configure globally
                path: 'M 0,0 L 10,5 L 0,10 Z', // Standard simple arrow path
                d: 5, // Offset from the target node
                fill: '#999'
            },
        },
        originalData: edge
    }));

    return { nodes: g6Nodes, edges: g6Edges };
};

interface KGGraphViewerProps {
    nodes: KGNode[];
    edges: KGEdge[];
    onNodeClick?: (nodeId: string, nodeData?: KGNode) => void;
    height?: number;
    width?: number;
}

const KGGraphViewer: React.FC<KGGraphViewerProps> = ({ 
    nodes, 
    edges, 
    onNodeClick, 
    height = 600, 
    width 
}) => {
    const graphContainerRef = useRef<HTMLDivElement>(null);
    const graphRef = useRef<Graph | null>(null);

    const graphData = useMemo(() => mapToG6Data(nodes, edges), [nodes, edges]);

    useEffect(() => {
        if (!graphContainerRef.current) return;

        const containerWidth = width || graphContainerRef.current.clientWidth || 800;
        const containerHeight = height;

        if (!graphRef.current) {
            const graphOptions: GraphOptions = {
                container: graphContainerRef.current,
                width: containerWidth,
                height: containerHeight,
                // fitView: true, // Removed from initial config, will call method later
                // fitViewPadding: [20, 40, 50, 20],
                layout: {
                    type: 'force', 
                    preventOverlap: true,
                    linkDistance: 150,
                    nodeStrength: -100,
                    edgeStrength: 0.1,
                },
                modes: {
                    default: ['drag-canvas', 'zoom-canvas', 'drag-node', {
                        type: 'tooltip',
                        formatText(model: any) { // Using any for now for model type from tooltip
                            if (!model) return '';
                            const node = model.originalData as KGNode | undefined;
                            if (node && node.properties) {
                                let tooltipText = `<b>ID:</b> ${node.id}<br/><b>Tag:</b> ${node.tag || 'N/A'}`;
                                Object.entries(node.properties).forEach(([key, value]) => {
                                    tooltipText += `<br/><b>${key}:</b> ${String(value)}`;
                                });
                                return tooltipText;
                            }
                            return model.label?.toString() || model.id?.toString() || '';
                        },
                    }],
                },
                defaultNode: {
                    size: 40,
                    // style is applied per node in mapToG6Data or can be set here as a fallback
                    labelCfg: {
                        style: {
                            fill: '#333',
                            fontSize: 10,
                        },
                        position: 'bottom',
                    },
                },
                defaultEdge: {
                    // Default style is now part of mapToG6Data for individual edges, 
                    // or can be partially set here if some aspects are truly global defaults
                    labelCfg: {
                        autoRotate: true,
                        style: {
                            fill: '#555',
                            fontSize: 9,
                        },
                    },
                },
            };
            graphRef.current = new Graph(graphOptions);
            
            if (graphData.nodes && graphData.nodes.length > 0) {
                graphRef.current.read(graphData); // Use read or setData for G6 v5
                graphRef.current.fitView([20,40,50,20]); // Call fitView after data is loaded
            }

            graphRef.current.on('node:click', (evt: IGraphEvent) => { 
                const { item } = evt;
                if (item && item.getModel) {
                    const model = item.getModel();
                    if (onNodeClick && model && model.id) {
                        onNodeClick(model.id as string, model.originalData as KGNode | undefined);
                    }
                }
            });

            const handleResize = () => {
                if (graphRef.current && graphContainerRef.current) {
                    graphRef.current.setSize(graphContainerRef.current.clientWidth, height);
                    graphRef.current.fitView([20,40,50,20]);
                }
            };
            window.addEventListener('resize', handleResize);

            return () => {
                if (graphRef.current) {
                    graphRef.current.destroy();
                    graphRef.current = null;
                }
                window.removeEventListener('resize', handleResize);
            };

        } else {
            graphRef.current.changeData(graphData); // For subsequent updates
            graphRef.current.fitView([20,40,50,20]); 
        }

    }, [graphData, height, width, onNodeClick]);

    // This useEffect might be redundant if the above useEffect handles data changes correctly.
    // Or, it can be used to specifically call render if data changes are not automatically re-rendering.
    useEffect(() => {
        if (graphRef.current) {
            // graphRef.current.read(graphData); // Data is now set in the main useEffect or via changeData
            // graphRef.current.render(); // G6 v5 typically auto-renders on data changes with changeData or read.
                                     // Explicit render might be needed if layout needs re-computation.
        }
    }, [graphData]);

    return <div ref={graphContainerRef} style={{ width: width || '100%', height: `${height}px`, border: '1px solid #eee' }} />;
};

export default KGGraphViewer; 