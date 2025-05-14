import axios from 'axios';
import { 
    DataSource, 
    CreateDataSourceRequest, 
    UpdateDataSourceRequest, 
    TestConnectionRequest, 
    TestConnectionResponse 
} from './types';

// 创建axios实例
const api = axios.create({
    // 使用绝对URL，直接指向后端服务
    baseURL: 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

// 暂时注释掉请求拦截器添加token
// api.interceptors.request.use((config) => {
//     const token = localStorage.getItem('token');
//     if (token) {
//         config.headers.Authorization = `Bearer ${token}`;
//     }
//     return config;
// });

export const dataSourcesApi = {
    // 获取所有数据源
    getDataSources: async (): Promise<DataSource[]> => {
        const response = await api.get('/data-sources');
        return response.data;
    },

    // 获取单个数据源
    getDataSource: async (id: string | number): Promise<DataSource> => {
        const response = await api.get(`/data-sources/${id}`);
        return response.data;
    },

    // 创建数据源
    createDataSource: async (dataSource: CreateDataSourceRequest): Promise<DataSource> => {
        // 处理连接参数转换 - 将常规参数转换为connection_params格式
        const { name, type, description, host, port, database, username, password, ...rest } = dataSource;
        
        // 根据数据源类型构建connection_params
        let connection_params: Record<string, any> = {};
        
        if (['MYSQL', 'POSTGRESQL', 'ORACLE', 'SQLSERVER'].includes(type)) {
            connection_params = {
                host,
                port,
                database,
                username,
                password,
                ...rest
            };
        } else if (['CSV', 'EXCEL'].includes(type)) {
            connection_params = {
                filePath: dataSource.filePath,
                ...rest
            };
        } else if (type === 'JSON') {
            connection_params = {
                jsonContent: dataSource.jsonContent,
                ...rest
            };
        }
        
        // 构建发送到API的请求体
        const requestBody = {
            name,
            type,
            description,
            connection_params
        };
        
        const response = await api.post('/data-sources', requestBody);
        return response.data;
    },

    // 更新数据源
    updateDataSource: async (id: string | number, dataSource: UpdateDataSourceRequest): Promise<DataSource> => {
        // 类似创建，处理连接参数转换
        const { name, type, description, host, port, database, username, password, ...rest } = dataSource;
        
        let connection_params: Record<string, any> = {};
        
        if (type && ['MYSQL', 'POSTGRESQL', 'ORACLE', 'SQLSERVER'].includes(type)) {
            connection_params = {
                ...(host !== undefined && { host }),
                ...(port !== undefined && { port }),
                ...(database !== undefined && { database }),
                ...(username !== undefined && { username }),
                ...(password !== undefined && { password }),
                ...rest
            };
        } else if (type && ['CSV', 'EXCEL'].includes(type)) {
            connection_params = {
                ...(dataSource.filePath && { filePath: dataSource.filePath }),
                ...rest
            };
        } else if (type === 'JSON') {
            connection_params = {
                ...(dataSource.jsonContent && { jsonContent: dataSource.jsonContent }),
                ...rest
            };
        }
        
        // 只包含存在的字段
        const requestBody: any = {};
        if (name) requestBody.name = name;
        if (type) requestBody.type = type;
        if (description !== undefined) requestBody.description = description;
        if (Object.keys(connection_params).length > 0) {
            requestBody.connection_params = connection_params;
        }
        
        const response = await api.put(`/data-sources/${id}`, requestBody);
        return response.data;
    },

    // 删除数据源
    deleteDataSource: async (id: string | number): Promise<void> => {
        await api.delete(`/data-sources/${id}`);
    },

    // 测试连接
    testConnection: async (data: TestConnectionRequest): Promise<TestConnectionResponse> => {
        // 转换为后端API期望的格式
        const { type, host, port, database, username, password, ...rest } = data;
        
        let connection_params: Record<string, any> = {};
        
        if (['MYSQL', 'POSTGRESQL', 'ORACLE', 'SQLSERVER'].includes(type)) {
            connection_params = {
                host,
                port,
                database,
                username,
                password,
                ...rest
            };
        } else if (['CSV', 'EXCEL'].includes(type)) {
            connection_params = {
                filePath: data.filePath,
                ...rest
            };
        } else if (type === 'JSON') {
            connection_params = {
                jsonContent: data.jsonContent,
                ...rest
            };
        }
        
        const requestBody = {
            type,
            name: 'temp_test_connection', // 临时名称，仅用于测试
            connection_params
        };
        
        const response = await api.post('/data-sources/test-connection', requestBody);
        return response.data;
    },

    // 同步数据源元数据
    syncMetadata: async (id: string | number): Promise<{message: string, status: string, tables_count: number, columns_count: number}> => {
        const response = await api.post(`/db-schema-metadata/data-sources/${id}/sync`);
        return response.data;
    },

    // 获取数据源所有表结构元数据
    getTableMetadata: async (id: string | number): Promise<any[]> => {
        const response = await api.get(`/db-schema-metadata/data-sources/${id}`);
        return response.data;
    },

    // 获取数据源表名列表
    getTablesList: async (id: string | number): Promise<string[]> => {
        const response = await api.get(`/db-schema-metadata/data-sources/${id}/tables`);
        return response.data;
    },

    // 自动处理数据源 - 新建数据源后的自动流程
    autoProcessDataSource: async (id: string | number): Promise<{success: boolean, messages: string[]}> => {
        try {
            const messages: string[] = [];
            
            // 1. 同步元数据
            const syncResult = await dataSourcesApi.syncMetadata(id);
            messages.push(`元数据同步成功: ${syncResult.tables_count}张表, ${syncResult.columns_count}个字段`);
            
            // 2. 分析表关系
            // 导入 dataModelingApi 避免循环依赖
            const { analyzeRelationships } = await import('../dataModeling/api').then(module => module.default);
            const relationshipResult = await analyzeRelationships(id);
            messages.push(`表关系分析成功: 发现${relationshipResult.count}个关系`);

            return {
                success: true,
                messages
            };
        } catch (error) {
            console.error('自动处理数据源失败:', error);
            return {
                success: false,
                messages: [(error as Error).message || '处理失败，请稍后重试']
            };
        }
    }
};

export default dataSourcesApi; 