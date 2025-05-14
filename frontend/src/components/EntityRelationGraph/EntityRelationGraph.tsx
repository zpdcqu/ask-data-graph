import React, { useState } from 'react';
import { Card, Row, Col, Space, Typography, Tooltip } from 'antd';

// 定义实体类型
export interface Entity {
  id: string;
  name: string;
  type: 'table';
  fields: Field[];
  description?: string;
}

// 定义字段类型
export interface Field {
  name: string;
  type: string;
  isPrimaryKey?: boolean;
  isForeignKey?: boolean;
  description?: string;
}

// 定义关系类型
export interface Relationship {
  id: string;
  source: string;
  target: string;
  relationshipType: 'N:1' | '1:N' | 'N:N' | '1:1';
  label?: string;
}

// 组件属性定义
interface EntityRelationGraphProps {
  entities: Entity[];
  relationships: Relationship[];
  width?: number | string;
  height?: number;
  onEntityClick?: (entityId: string) => void;
}

const { Text } = Typography;

const EntityRelationGraph: React.FC<EntityRelationGraphProps> = ({
  entities,
  relationships,
  width = '100%',
  height = 600,
  onEntityClick,
}) => {
  const [hoveredRelationship, setHoveredRelationship] = useState<string | null>(null);

  // 计算实体位置
  const calculateEntityPositions = () => {
    // 简单的布局，将实体分为左中右三列
    const entityPositions: Record<string, { x: number, y: number }> = {};
    
    // 找出所有作为源的实体
    const sourcesOnly = entities.filter(entity => 
      relationships.some(rel => rel.source === entity.id) && 
      !relationships.some(rel => rel.target === entity.id)
    );
    
    // 找出所有作为目标的实体
    const targetsOnly = entities.filter(entity => 
      relationships.some(rel => rel.target === entity.id) && 
      !relationships.some(rel => rel.source === entity.id)
    );
    
    // 既是源又是目标的实体
    const middle = entities.filter(entity => 
      relationships.some(rel => rel.source === entity.id) && 
      relationships.some(rel => rel.target === entity.id)
    );
    
    // 孤立的实体（既不是源也不是目标）
    const isolated = entities.filter(entity => 
      !relationships.some(rel => rel.source === entity.id || rel.target === entity.id)
    );
    
    // 布局：源实体放左边，目标实体放右边，中间实体放中间，孤立实体放最右边
    const leftEntities = sourcesOnly.length > 0 ? sourcesOnly : (middle.length > 0 ? [middle[0]] : (entities.length > 0 ? [entities[0]] : []));
    const rightEntities = targetsOnly.length > 0 ? targetsOnly : isolated;
    const middleEntities = middle.filter(e => !leftEntities.includes(e));
    
    // 计算位置
    const containerWidth = typeof width === 'number' ? width : 1000; // 假设容器宽度
    const containerHeight = typeof height === 'number' ? height : 600; // 假设容器高度
    
    // 左侧实体
    leftEntities.forEach((entity, index) => {
      entityPositions[entity.id] = {
        x: containerWidth * 0.2,
        y: (containerHeight / (leftEntities.length + 1)) * (index + 1)
      };
    });
    
    // 中间实体
    middleEntities.forEach((entity, index) => {
      entityPositions[entity.id] = {
        x: containerWidth * 0.5,
        y: (containerHeight / (middleEntities.length + 1)) * (index + 1)
      };
    });
    
    // 右侧实体
    rightEntities.forEach((entity, index) => {
      entityPositions[entity.id] = {
        x: containerWidth * 0.8,
        y: (containerHeight / (rightEntities.length + 1)) * (index + 1)
      };
    });
    
    return entityPositions;
  };
  
  const entityPositions = calculateEntityPositions();
  
  // 绘制实体卡片
  const renderEntityCard = (entity: Entity) => {
    const position = entityPositions[entity.id] || { x: 0, y: 0 };
    
    return (
      <Card
        key={entity.id}
        title={entity.name}
        size="small"
        style={{
          width: 200,
          position: 'absolute',
          left: position.x - 100, // 居中
          top: position.y - 100,
          cursor: 'pointer',
          border: '1px solid #91D5FF',
          borderRadius: '4px',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.09)',
          zIndex: 10
        }}
        headStyle={{ 
          background: '#E6F7FF',
          borderBottom: '1px solid #91D5FF',
        }}
        onClick={() => onEntityClick && onEntityClick(entity.id)}
      >
        <div style={{ maxHeight: '150px', overflow: 'auto' }}>
          {entity.fields.map((field, index) => (
            <div 
              key={index} 
              style={{ 
                padding: '4px 0',
                borderBottom: index < entity.fields.length - 1 ? '1px solid #f0f0f0' : 'none',
                display: 'flex',
                justifyContent: 'space-between'
              }}
            >
              <Space>
                {field.isPrimaryKey && <Tooltip title="主键"><Text>🔑</Text></Tooltip>}
                {field.isForeignKey && <Tooltip title="外键"><Text>🔗</Text></Tooltip>}
                <Text style={{ fontSize: '12px' }}>{field.name}</Text>
              </Space>
              <Text type="secondary" style={{ fontSize: '12px' }}>{field.type}</Text>
            </div>
          ))}
        </div>
      </Card>
    );
  };
  
  // 绘制关系线
  const renderRelationships = () => {
    return relationships.map(relationship => {
      const sourcePos = entityPositions[relationship.source];
      const targetPos = entityPositions[relationship.target];
      
      if (!sourcePos || !targetPos) return null;
      
      // 计算线的起点和终点
      const startX = sourcePos.x;
      const startY = sourcePos.y;
      const endX = targetPos.x;
      const endY = targetPos.y;
      
      // 计算线的长度和角度
      const length = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
      const angle = Math.atan2(endY - startY, endX - startX) * 180 / Math.PI;
      
      // 确定关系类型样式
      const isHighlighted = hoveredRelationship === relationship.id;
      
      return (
        <div 
          key={relationship.id}
          style={{
            position: 'absolute',
            left: startX,
            top: startY,
            width: length,
            height: 2,
            backgroundColor: isHighlighted ? '#1890ff' : '#91D5FF',
            transformOrigin: '0 0',
            transform: `rotate(${angle}deg)`,
            zIndex: 5
          }}
          onMouseEnter={() => setHoveredRelationship(relationship.id)}
          onMouseLeave={() => setHoveredRelationship(null)}
        >
          {/* 关系标签 */}
          <div 
            style={{
              position: 'absolute',
              left: length / 2 - 15,
              top: -15,
              backgroundColor: '#fff',
              border: '1px solid #91D5FF',
              borderRadius: '4px',
              padding: '0 4px',
              fontSize: '12px',
              lineHeight: '20px',
              textAlign: 'center',
              width: '30px',
              transform: `rotate(-${angle}deg)`, // 反向旋转使文字保持水平
              zIndex: 6
            }}
          >
            {relationship.relationshipType}
          </div>
          
          {/* 箭头 */}
          <div 
            style={{
              position: 'absolute',
              right: 0,
              top: -4,
              width: 0,
              height: 0,
              borderTop: '5px solid transparent',
              borderBottom: '5px solid transparent',
              borderLeft: `8px solid ${isHighlighted ? '#1890ff' : '#91D5FF'}`,
              transform: 'translateX(100%)',
            }}
          />
        </div>
      );
    });
  };
  
  return (
    <div 
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : `${height}px`,
        border: '1px solid #eee',
        borderRadius: '4px',
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#fafafa'
      }}
    >
      {/* 渲染关系线 */}
      {renderRelationships()}
      
      {/* 渲染实体卡片 */}
      {entities.map(entity => renderEntityCard(entity))}
    </div>
  );
};

export default EntityRelationGraph; 