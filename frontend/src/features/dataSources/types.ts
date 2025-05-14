// 数据源类型枚举
export enum DataSourceType {
    MYSQL = 'MYSQL',
    POSTGRESQL = 'POSTGRESQL',
    ORACLE = 'ORACLE',
    SQLSERVER = 'SQLSERVER',
    CSV = 'CSV',
    EXCEL = 'EXCEL',
    JSON = 'JSON',
    // 可以根据需要扩展其他类型
}

// 数据源基本信息接口
export interface DataSource {
    id: string | number;
    name: string;
    type: DataSourceType;
    host?: string;
    port?: number;
    database?: string;
    username?: string;
    password?: string;
    description?: string;
    createdAt?: string;
    updatedAt?: string;
    status?: 'active' | 'inactive' | 'error';
    createdBy?: string;
    // 特定类型数据源的字段
    filePath?: string; // CSV, Excel文件路径
    jsonContent?: string; // JSON内容
    // 其他可能的连接参数
    connectionParams?: Record<string, any>;
}

// 创建/更新数据源的请求接口
export interface CreateDataSourceRequest {
    name: string;
    type: DataSourceType;
    host?: string;
    port?: number;
    database?: string;
    username?: string;
    password?: string;
    description?: string;
    // 特定类型数据源的字段
    filePath?: string; // CSV, Excel文件路径
    jsonContent?: string; // JSON内容
    connectionParams?: Record<string, any>;
}

// 更新请求接口
export type UpdateDataSourceRequest = Partial<CreateDataSourceRequest> & { id?: string | number };

// 数据源测试连接请求
export interface TestConnectionRequest {
    type: DataSourceType;
    host?: string;
    port?: number;
    database?: string;
    username?: string;
    password?: string;
    // 特定类型数据源的字段
    filePath?: string; // CSV, Excel文件路径
    jsonContent?: string; // JSON内容
    connectionParams?: Record<string, any>;
}

// 数据源测试连接响应
export interface TestConnectionResponse {
    success: boolean;
    message?: string;
    status?: string; // 添加状态字段，与后端API返回一致
} 