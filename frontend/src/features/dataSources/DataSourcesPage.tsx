import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Typography, Tag, Popconfirm, message, Input, Row, Col, Tooltip, Modal } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, CheckCircleOutlined, ExclamationCircleOutlined, ApiOutlined, SyncOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { DataSource, DataSourceType, CreateDataSourceRequest, UpdateDataSourceRequest } from './types';
import DataSourceFormModal from './DataSourceFormModal';
import dataSourcesApi from './api';
import axios from 'axios';

const { Title } = Typography;

const DataSourcesPage: React.FC = () => {
    const [dataSources, setDataSources] = useState<DataSource[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchText, setSearchText] = useState('');
    const [modalVisible, setModalVisible] = useState(false);
    const [currentDataSource, setCurrentDataSource] = useState<DataSource | null>(null);
    const [processingId, setProcessingId] = useState<string | number | null>(null);
    const [autoProcessMessages, setAutoProcessMessages] = useState<string[]>([]);
    const [messageModalVisible, setMessageModalVisible] = useState(false);

    // 加载数据源列表
    const fetchDataSources = async () => {
        setLoading(true);
        try {
            console.log('正在获取数据源...');
            const data = await dataSourcesApi.getDataSources();
            console.log('获取成功, 数据:', data);
            
            // 处理后端返回的数据，将connection_params转为前端的connectionParams
            const processedData = data.map(ds => ({
                ...ds,
                connectionParams: (ds as any).connection_params, // 使用类型断言
            }));
            
            setDataSources(processedData);
        } catch (error) {
            console.error('获取数据源失败:', error);
            if (axios.isAxiosError(error)) {
                console.error('请求详情:', error.config);
                console.error('响应详情:', error.response);
            }
            message.error('获取数据源列表失败，请稍后重试');
        } finally {
            setLoading(false);
        }
    };

    // 测试API连接
    const testApiConnection = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/v1/data-sources/test');
            console.log('测试API返回:', response.data);
            message.success('API连接测试成功');
        } catch (error) {
            console.error('API连接测试失败:', error);
            message.error('API连接测试失败');
        }
    };

    // 初始加载
    useEffect(() => {
        fetchDataSources();
    }, []);

    // 处理搜索
    const filteredDataSources = dataSources.filter(ds => 
        ds.name.toLowerCase().includes(searchText.toLowerCase()) ||
        ds.connectionParams?.database?.toString().toLowerCase().includes(searchText.toLowerCase()) ||
        ds.connectionParams?.host?.toString().toLowerCase().includes(searchText.toLowerCase())
    );

    // 打开编辑模态框
    const handleEdit = (dataSource: DataSource) => {
        // 将connectionParams中的字段提取到顶层
        const editableDataSource = {
            ...dataSource,
            host: dataSource.connectionParams?.host,
            port: dataSource.connectionParams?.port,
            database: dataSource.connectionParams?.database,
            username: dataSource.connectionParams?.username,
            password: dataSource.connectionParams?.password,
        };
        
        setCurrentDataSource(editableDataSource);
        setModalVisible(true);
    };

    // 处理删除
    const handleDelete = async (id: string | number) => {
        setLoading(true);
        try {
            await dataSourcesApi.deleteDataSource(id);
            message.success('数据源已删除');
            // 重新加载数据源列表
            fetchDataSources();
        } catch (error) {
            console.error('删除数据源失败:', error);
            message.error('删除失败，请稍后重试');
        } finally {
            setLoading(false);
        }
    };

    // 自动处理数据源 - 同步元数据和分析表关系
    const handleAutoProcess = async (id: string | number) => {
        setProcessingId(id);
        setAutoProcessMessages([]);
        try {
            // 显示加载提示
            const loadingMsg = message.loading({ content: '正在处理数据源...', key: 'autoProcess', duration: 0 });
            
            // 开始自动处理
            const result = await dataSourcesApi.autoProcessDataSource(id);
            
            // 关闭加载提示
            loadingMsg();
            
            // 显示处理结果
            if (result.success) {
                message.success('数据源处理成功');
                setAutoProcessMessages(result.messages);
                setMessageModalVisible(true);
            } else {
                message.error('处理失败: ' + result.messages[0]);
            }
            
            // 重新加载数据源列表
            fetchDataSources();
        } catch (error) {
            console.error('处理数据源失败:', error);
            message.error('处理失败，请稍后重试');
        } finally {
            setProcessingId(null);
        }
    };

    // 处理模态框保存
    const handleFormSave = async (values: DataSource, autoProcess: boolean) => {
        setLoading(true);
        try {
            let savedDataSource: DataSource;
            
            if (currentDataSource) {
                // 更新现有数据源 - 移除id字段，避免重复
                const { id, ...updateData } = values;
                savedDataSource = await dataSourcesApi.updateDataSource(currentDataSource.id, updateData);
                message.success('数据源已更新');
            } else {
                // 添加新数据源
                savedDataSource = await dataSourcesApi.createDataSource(values as CreateDataSourceRequest);
                message.success('数据源已创建');
                
                // 如果勾选了自动处理，则自动进行元数据同步和表关系分析
                if (autoProcess) {
                    // 关闭当前表单模态框
                    setModalVisible(false);
                    setCurrentDataSource(null);
                    
                    // 启动自动处理
                    await handleAutoProcess(savedDataSource.id);
                    return; // 提前返回，避免重复刷新
                }
            }
            
            // 关闭模态框并重新加载数据
            setModalVisible(false);
            setCurrentDataSource(null);
            fetchDataSources();
        } catch (error) {
            console.error('保存数据源失败:', error);
            message.error('保存失败，请稍后重试');
        } finally {
            setLoading(false);
        }
    };

    // 表格列定义
    const columns: ColumnsType<DataSource> = [
        {
            title: '名称',
            dataIndex: 'name',
            key: 'name',
            sorter: (a, b) => a.name.localeCompare(b.name),
        },
        {
            title: '类型',
            dataIndex: 'type',
            key: 'type',
            render: (type: DataSourceType) => <span>{type}</span>,
            // 使用正确的过滤器类型
            filters: Object.values(DataSourceType).map(type => ({ 
                text: type, 
                value: type 
            })),
            onFilter: (value, record) => record.type === value,
        },
        {
            title: '主机',
            key: 'host',
            render: (_, record) => record.connectionParams?.host || '',
        },
        {
            title: '端口',
            key: 'port',
            render: (_, record) => record.connectionParams?.port || '',
        },
        {
            title: '数据库',
            key: 'database',
            render: (_, record) => record.connectionParams?.database || '',
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            render: (status?: string) => {
                if (!status) return null;
                const statusMap = {
                    active: { color: 'success', text: '正常', icon: <CheckCircleOutlined /> },
                    inactive: { color: 'warning', text: '未启用', icon: <ExclamationCircleOutlined /> },
                    error: { color: 'error', text: '错误', icon: <ExclamationCircleOutlined /> },
                    pending_test: { color: 'processing', text: '待测试', icon: <ExclamationCircleOutlined /> },
                };
                const statusInfo = statusMap[status as keyof typeof statusMap] || statusMap.inactive;
                return (
                    <Tag color={statusInfo.color} icon={statusInfo.icon}>
                        {statusInfo.text}
                    </Tag>
                );
            },
            filters: [
                { text: '正常', value: 'active' },
                { text: '未启用', value: 'inactive' },
                { text: '错误', value: 'error' },
                { text: '待测试', value: 'pending_test' },
            ],
            onFilter: (value, record) => record.status === value,
        },
        {
            title: '操作',
            key: 'action',
            render: (_, record) => (
                <Space size="middle">
                    <Button type="text" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
                        编辑
                    </Button>
                    <Tooltip title="处理数据源：同步元数据和分析表关系">
                        <Button 
                            type="text" 
                            icon={<SyncOutlined spin={processingId === record.id} />} 
                            onClick={() => handleAutoProcess(record.id)}
                            loading={processingId === record.id}
                        >
                            处理
                        </Button>
                    </Tooltip>
                    <Popconfirm
                        title="确定删除此数据源吗？"
                        description="此操作不可撤销，关联的数据可能受到影响。"
                        onConfirm={() => handleDelete(record.id)}
                        okText="确定"
                        cancelText="取消"
                    >
                        <Button type="text" danger icon={<DeleteOutlined />}>
                            删除
                        </Button>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <div>
            <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
                <Col>
                    <Title level={2}>数据源连接</Title>
                </Col>
                <Col>
                    <Space>
                        <Button onClick={testApiConnection}>测试API连接</Button>
                        <Input 
                            placeholder="搜索数据源..." 
                            value={searchText}
                            onChange={e => setSearchText(e.target.value)}
                            allowClear
                            prefix={<SearchOutlined />}
                            style={{ width: 200 }}
                        />
                        <Button 
                            type="primary" 
                            icon={<PlusOutlined />} 
                            onClick={() => {
                                setCurrentDataSource(null);
                                setModalVisible(true);
                            }}
                        >
                            新建连接
                        </Button>
                    </Space>
                </Col>
            </Row>

            <Table 
                columns={columns}
                dataSource={filteredDataSources}
                rowKey="id"
                loading={loading}
                pagination={{ 
                    showSizeChanger: true,
                    showTotal: total => `共 ${total} 项`
                }}
            />

            {/* 数据源表单模态框 */}
            <DataSourceFormModal 
                visible={modalVisible}
                dataSource={currentDataSource}
                onCancel={() => {
                    setModalVisible(false);
                    setCurrentDataSource(null);
                }}
                onSave={handleFormSave}
            />

            {/* 自动处理结果显示模态框 */}
            <Modal
                title="数据源处理结果"
                open={messageModalVisible}
                onOk={() => setMessageModalVisible(false)}
                onCancel={() => setMessageModalVisible(false)}
                footer={[
                    <Button key="ok" type="primary" onClick={() => setMessageModalVisible(false)}>
                        确定
                    </Button>
                ]}
            >
                <ul>
                    {autoProcessMessages.map((msg, index) => (
                        <li key={index}>{msg}</li>
                    ))}
                </ul>
            </Modal>
        </div>
    );
};

export default DataSourcesPage; 