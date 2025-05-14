import React, { useState, useEffect, useCallback } from 'react';
import { Input, Spin, Alert, Row, Col, Typography, Card, Button, Space, InputNumber, Select } from 'antd';
import KGGraphViewer from '../../components/KGGraphViewer';
import { 
    fetchNeighbors, 
    searchNodes, 
    clearGraphData,
    setCurrentCentralNodeId 
} from './kgVisualizationSlice';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { KGNode, KGEdge } from './kgVisualizationApi';

const { Search } = Input;
const { Title, Text } = Typography;
const { Option } = Select;

const KGVisualizationPage: React.FC = () => {
    const dispatch = useAppDispatch();
    const { 
        nodes, 
        edges, 
        status, 
        error,
        currentCentralNodeId
    } = useAppSelector((state) => state.kgVisualization);

    const [searchTerm, setSearchTerm] = useState<string>('');
    const [selectedNodeInfo, setSelectedNodeInfo] = useState<KGNode | null>(null);

    // Configuration for fetching neighbors
    const [hops, setHops] = useState<number>(1);
    const [limitPerNode, setLimitPerNode] = useState<number>(25); // Default from backend
    const [targetEdgeTypes, setTargetEdgeTypes] = useState<string[]>([]); // e.g. ['FRIEND_OF', 'WORKS_AT']

    // Debounce search if desired, or handle directly onSearch
    const handleSearch = (value: string) => {
        if (value.trim()) {
            dispatch(clearGraphData()); // Clear previous graph before new search
            dispatch(searchNodes({ queryString: value.trim(), limit: 50 }));
            setSelectedNodeInfo(null);
        }
    };

    const handleNodeClick = useCallback((nodeId: string, nodeData?: KGNode) => {
        if (nodeId) {
            dispatch(setCurrentCentralNodeId(nodeId));
            dispatch(fetchNeighbors({ 
                nodeId: nodeId, 
                hops: hops, 
                limitPerNode: limitPerNode,
                targetEdgeTypes: targetEdgeTypes.length > 0 ? targetEdgeTypes : undefined
            }));
            setSelectedNodeInfo(nodeData || null);
        }
    }, [dispatch, hops, limitPerNode, targetEdgeTypes]);

    const handleClearGraph = () => {
        dispatch(clearGraphData());
        setSelectedNodeInfo(null);
        setSearchTerm('');
    };

    // Effect to potentially fetch initial data or handle central node changes
    // For example, if currentCentralNodeId is set from outside or on initial load with a default ID
    // useEffect(() => {
    //     if (currentCentralNodeId && nodes.length === 0) { // Fetch if central node is set but no graph shown
    //         handleNodeClick(currentCentralNodeId);
    //     }
    // }, [currentCentralNodeId, nodes, handleNodeClick]);

    return (
        <div style={{ padding: '20px' }}>
            <Title level={2}>Knowledge Graph Visualization</Title>
            
            <Row gutter={[16, 16]} style={{ marginBottom: '20px' }}>
                <Col xs={24} sm={12} md={8} lg={6}>
                    <Search
                        placeholder="Search for nodes (e.g., by name)"
                        enterButton="Search"
                        size="large"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        onSearch={handleSearch}
                    />
                </Col>
                <Col xs={24} sm={12} md={16} lg={18}>
                    <Space wrap>
                        <Text>Hops:</Text>
                        <InputNumber min={1} max={5} value={hops} onChange={(value) => setHops(value || 1)} />
                        <Text>Limit/Node:</Text>
                        <InputNumber min={5} max={100} value={limitPerNode} onChange={(value) => setLimitPerNode(value || 25)} />
                        {/* TODO: Add Select for targetEdgeTypes if schema is known or fetched */}
                        {/* <Text>Edge Types (CSV):</Text>
                        <Input 
                            placeholder="e.g., FOLLOWS,WORKS_AT"
                            style={{width: 200}}
                            onChange={(e) => setTargetEdgeTypes(e.target.value.split(',').map(s => s.trim()).filter(s => s))}
                        /> */}
                        <Button onClick={handleClearGraph} danger>
                            Clear Graph
                        </Button>
                    </Space>
                </Col>
            </Row>

            {status === 'loading' && <Spin tip="Loading graph data..." size="large" style={{ display: 'block', marginTop: '20px' }} />}
            {status === 'failed' && error && <Alert message="Error" description={error} type="error" showIcon style={{ marginTop: '20px' }} />}
            
            <Row gutter={[16, 16]}>
                <Col xs={24} md={selectedNodeInfo ? 18 : 24}>
                    <div style={{ height: '70vh', width: '100%', position: 'relative' }}> 
                        { (nodes.length > 0 || edges.length > 0 || status === 'loading') ? (
                            <KGGraphViewer 
                                nodes={nodes} 
                                edges={edges} 
                                onNodeClick={handleNodeClick} 
                                height={650} // Example height
                            />
                        ) : (
                            <div style={{
                                display: 'flex', 
                                justifyContent: 'center', 
                                alignItems: 'center', 
                                height: '100%', 
                                border: '1px dashed #ccc',
                                borderRadius: '4px'
                            }}>
                                <Text type="secondary">Search for a node or click on one to explore the graph.</Text>
                            </div>
                        )}
                    </div>
                </Col>
                {selectedNodeInfo && (
                    <Col xs={24} md={6}>
                        <Card title={`Node Details: ${selectedNodeInfo.label || selectedNodeInfo.id}`}>
                            <Text strong>ID: </Text><Text>{selectedNodeInfo.id}</Text><br/>
                            <Text strong>Tag: </Text><Text>{selectedNodeInfo.tag || 'N/A'}</Text><br/>
                            {selectedNodeInfo.properties && Object.entries(selectedNodeInfo.properties).map(([key, value]) => (
                                <div key={key}>
                                    <Text strong>{key}: </Text><Text>{String(value)}</Text>
                                </div>
                            ))}
                            <Button 
                                type="primary" 
                                style={{marginTop: '15px'}}
                                onClick={() => handleNodeClick(selectedNodeInfo.id, selectedNodeInfo)}
                                block
                            >
                                Explore Neighbors (Re-fetch)
                            </Button>
                        </Card>
                    </Col>
                )}
            </Row>
        </div>
    );
};

export default KGVisualizationPage; 