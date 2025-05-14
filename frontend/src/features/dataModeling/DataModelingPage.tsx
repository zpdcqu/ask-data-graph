import React, { useState, useEffect } from 'react';
import { Card, Button, Input, Select, Space, Typography, Row, Col, Tooltip, message, Spin, Empty } from 'antd';
import EntityRelationGraph, { Entity, Field, Relationship } from '../../components/EntityRelationGraph';
import dataModelingApi from './api';

const { Title, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

// 从后端数据结构到前端格式的转换
const convertToEntityModel = (nodes: any[]): Entity[] => {
  return nodes.map(node => ({
    id: node.id,
    name: node.label,
    type: 'table',
    fields: node.columns.map((col: any) => ({
      name: col.name,
      type: col.data_type + (col.size ? `(${col.size})` : ''),
      isPrimaryKey: col.is_primary_key,
      isForeignKey: col.is_foreign_key,
      description: col.description
    }))
  }));
};

// 从后端关系到前端格式的转换
const convertToRelationshipModel = (edges: any[]): Relationship[] => {
  return edges.map(edge => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    relationshipType: edge.label || getRelationshipTypeLabel(edge.relationship_type)
  }));
};

// 获取关系类型标签
const getRelationshipTypeLabel = (type: string): string => {
  switch (type) {
    case 'one_to_one': return '1:1';
    case 'one_to_many': return '1:N';
    case 'many_to_many': return 'N:M';
    default: return 'N:1';
  }
};

const DataModelingPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [dataSources, setDataSources] = useState<any[]>([]);
  const [selectedDataSourceId, setSelectedDataSourceId] = useState<string | number | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);
  const [diagramId, setDiagramId] = useState<string | number | null>(null);

  // 加载数据源
  useEffect(() => {
    const fetchDataSources = async () => {
      try {
        // 从dataSources模块导入API
        const { getDataSources } = await import('../dataSources/api').then(module => module.default);
        const sources = await getDataSources();
        setDataSources(sources);
        
        // 如果有数据源，默认选择第一个
        if (sources.length > 0) {
          setSelectedDataSourceId(sources[0].id);
        }
      } catch (error) {
        console.error('获取数据源失败:', error);
        message.error('获取数据源列表失败');
      }
    };
    
    fetchDataSources();
  }, []);

  // 当选择数据源变更时加载ER图数据
  useEffect(() => {
    if (!selectedDataSourceId) return;
    
    const fetchERData = async () => {
      setLoading(true);
      try {
        const data = await dataModelingApi.getDiagramData(selectedDataSourceId, diagramId || undefined);
        
        // 转换数据格式
        const entityModels = convertToEntityModel(data.nodes);
        const relationshipModels = convertToRelationshipModel(data.edges);
        
        setEntities(entityModels);
        setRelationships(relationshipModels);
        
        // 重置选中的实体
        setSelectedEntityId(null);
      } catch (error) {
        console.error('获取ER图数据失败:', error);
        message.error('获取ER图数据失败，请确保数据源已经完成元数据同步和表关系分析');
        // 清空实体和关系
        setEntities([]);
        setRelationships([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchERData();
  }, [selectedDataSourceId, diagramId]);

  // 获取选中的实体信息
  const selectedEntity = selectedEntityId 
    ? entities.find(e => e.id === selectedEntityId) 
    : null;

  // 处理实体点击事件
  const handleEntityClick = (entityId: string) => {
    setSelectedEntityId(entityId);
  };

  // 搜索实体
  const handleSearch = (value: string) => {
    if (!value) return;
    const foundEntity = entities.find(e => 
      e.id.toLowerCase().includes(value.toLowerCase()) || 
      e.name.toLowerCase().includes(value.toLowerCase())
    );
    if (foundEntity) {
      setSelectedEntityId(foundEntity.id);
    }
  };

  // 处理数据源变更
  const handleDataSourceChange = (value: string | number) => {
    setSelectedDataSourceId(value);
  };

  return (
    <div style={{ padding: '20px' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: '16px' }}>
        <Col>
          <Title level={4}>数据建模</Title>
        </Col>
        <Col>
          <Space>
            <Select
              placeholder="选择数据源"
              style={{ width: 200 }}
              value={selectedDataSourceId}
              onChange={handleDataSourceChange}
            >
              {dataSources.map(ds => (
                <Option key={ds.id} value={ds.id}>{ds.name}</Option>
              ))}
            </Select>
            {loading && <Spin />}
          </Space>
        </Col>
      </Row>
      
      {entities.length > 0 ? (
        <Row gutter={20}>
          {/* 左侧面板 */}
          <Col span={6}>
            <Card title="实体列表" size="small" bordered style={{ marginBottom: '16px' }}>
              <Search
                placeholder="搜索实体..."
                onSearch={handleSearch}
                style={{ marginBottom: '16px' }}
              />
              <div style={{ height: '300px', overflowY: 'auto' }}>
                {entities.map(entity => (
                  <div 
                    key={entity.id}
                    onClick={() => setSelectedEntityId(entity.id)}
                    style={{
                      padding: '8px 12px',
                      cursor: 'pointer',
                      backgroundColor: selectedEntityId === entity.id ? '#e6f7ff' : 'transparent',
                      borderRadius: '4px',
                      marginBottom: '4px'
                    }}
                  >
                    {entity.name}
                  </div>
                ))}
              </div>
            </Card>
            
            {selectedEntity && (
              <Card title="实体详情" size="small" bordered>
                <div style={{ marginBottom: '8px' }}>
                  <Text strong>表名：</Text> {selectedEntity.name}
                </div>
                <div>
                  <Text strong>字段：</Text>
                  <ul style={{ paddingLeft: '20px', marginTop: '8px' }}>
                    {selectedEntity.fields.map((field, index) => (
                      <li key={index}>
                        <Space>
                          {field.isPrimaryKey && <Tooltip title="主键"><span>🔑</span></Tooltip>}
                          {field.isForeignKey && <Tooltip title="外键"><span>🔗</span></Tooltip>}
                          <Text>{field.name}</Text>
                          <Text type="secondary">{field.type}</Text>
                        </Space>
                      </li>
                    ))}
                  </ul>
                </div>
              </Card>
            )}
          </Col>
          
          {/* 主要图形区域 */}
          <Col span={18}>
            <Card bordered>
              <EntityRelationGraph 
                entities={entities}
                relationships={relationships}
                height={600}
                onEntityClick={handleEntityClick}
              />
            </Card>
          </Col>
        </Row>
      ) : (
        <Card style={{ textAlign: 'center', padding: '40px 0' }}>
          <Empty
            description={
              <span>
                {selectedDataSourceId 
                  ? '未找到ER图数据，请先在数据源管理页面完成元数据同步和表关系分析' 
                  : '请选择一个数据源'}
              </span>
            }
          >
            {selectedDataSourceId && (
              <Button 
                type="primary" 
                onClick={() => {
                  // 前往数据源页面
                  window.location.href = '#/data-sources';
                }}
              >
                前往数据源管理
              </Button>
            )}
          </Empty>
        </Card>
      )}
    </div>
  );
};

export default DataModelingPage; 