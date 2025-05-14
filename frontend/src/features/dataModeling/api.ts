import axios from 'axios';
import { ERDiagramData, TableRelationship, ERDiagram } from './types';

// 创建axios实例
const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

export const dataModelingApi = {
    // 获取ER图数据
    getDiagramData: async (dataSourceId: number | string, diagramId?: number | string): Promise<ERDiagramData> => {
        const url = diagramId 
            ? `/er-diagrams/data-sources/${dataSourceId}/diagram-data?diagram_id=${diagramId}`
            : `/er-diagrams/data-sources/${dataSourceId}/diagram-data`;
        const response = await api.get(url);
        return response.data;
    },

    // 分析表关系
    analyzeRelationships: async (dataSourceId: number | string): Promise<{message: string, status: string, count: number}> => {
        const response = await api.post(`/er-diagrams/data-sources/${dataSourceId}/analyze-relationships`);
        return response.data;
    },

    // 获取表关系列表
    getRelationships: async (dataSourceId: number | string): Promise<TableRelationship[]> => {
        const response = await api.get(`/er-diagrams/data-sources/${dataSourceId}/relationships`);
        return response.data;
    },

    // 更新表关系
    updateRelationship: async (relationshipId: number | string, data: Partial<TableRelationship>): Promise<TableRelationship> => {
        const response = await api.put(`/er-diagrams/relationships/${relationshipId}`, data);
        return response.data;
    },

    // 创建ER图配置
    createDiagram: async (dataSourceId: number | string, name: string, description?: string): Promise<ERDiagram> => {
        const response = await api.post(`/er-diagrams/data-sources/${dataSourceId}/diagrams`, {
            data_source_id: dataSourceId,
            name,
            description
        });
        return response.data;
    },

    // 更新ER图配置
    updateDiagram: async (diagramId: number | string, data: Partial<ERDiagram>): Promise<ERDiagram> => {
        const response = await api.put(`/er-diagrams/diagrams/${diagramId}`, data);
        return response.data;
    },

    // 保存ER图布局
    saveDiagramLayout: async (diagramId: number | string, layoutData: any): Promise<ERDiagram> => {
        const response = await api.put(`/er-diagrams/diagrams/${diagramId}`, {
            layout_data: layoutData
        });
        return response.data;
    }
};

export default dataModelingApi; 