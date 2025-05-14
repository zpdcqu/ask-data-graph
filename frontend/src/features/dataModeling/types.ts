import { RelationshipType } from './constants';

// 表列信息
export interface TableColumn {
    name: string;
    data_type: string;
    size?: number;
    is_primary_key: boolean;
    is_foreign_key: boolean;
    description?: string;
}

// 表节点
export interface TableNode {
    id: string;
    label: string;
    columns: TableColumn[];
    position?: {
        x: number;
        y: number;
    };
}

// 关系边
export interface RelationshipEdge {
    id: string;
    source: string;
    target: string;
    relationship_type: string;
    source_columns: string[];
    target_columns: string[];
    label?: string;
}

// 完整ER图数据
export interface ERDiagramData {
    nodes: TableNode[];
    edges: RelationshipEdge[];
    settings?: any;
}

// 表关系基本信息
export interface TableRelationship {
    id: number;
    data_source_id: number;
    source_table: string;
    target_table: string;
    relationship_type: string;
    source_columns: string[];
    target_columns: string[];
    is_identified: string;
    confidence_score?: number;
    description?: string;
    created_at: string;
    updated_at: string;
}

// ER图配置
export interface ERDiagram {
    id: number;
    data_source_id: number;
    name: string;
    description?: string;
    layout_data?: any;
    display_settings?: any;
    created_at: string;
    updated_at: string;
} 