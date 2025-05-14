import React, { useEffect, useState } from 'react';
import { Modal, Form, Input, Select, InputNumber, Button, Space, message, Divider } from 'antd';
import { DatabaseOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { DataSource, DataSourceType, TestConnectionRequest } from './types';
import dataSourcesApi from './api';

interface DataSourceFormModalProps {
    visible: boolean;
    dataSource: DataSource | null;
    onCancel: () => void;
    onSave: (dataSource: DataSource) => void;
}

const { Option } = Select;

const DataSourceFormModal: React.FC<DataSourceFormModalProps> = ({
    visible,
    dataSource,
    onCancel,
    onSave
}) => {
    const [form] = Form.useForm();
    const [testLoading, setTestLoading] = useState(false);
    const [selectedType, setSelectedType] = useState<DataSourceType>(dataSource?.type || DataSourceType.MYSQL);

    // 当dataSource变化时，重置表单
    useEffect(() => {
        if (visible) {
            form.resetFields();
            if (dataSource) {
                form.setFieldsValue(dataSource);
                setSelectedType(dataSource.type);
            } else {
                form.setFieldsValue({ type: DataSourceType.MYSQL });
                setSelectedType(DataSourceType.MYSQL);
            }
        }
    }, [visible, dataSource, form]);

    // 测试连接
    const handleTestConnection = async () => {
        try {
            // 先验证表单当前值
            await form.validateFields(['type', 'host', 'port', 'database', 'username', 'password']);
            const values = form.getFieldsValue();
            
            setTestLoading(true);
            
            try {
                // 使用API进行测试连接
                const result = await dataSourcesApi.testConnection(values as TestConnectionRequest);
                
                // 根据API响应显示成功或失败消息
                if (result.status === 'success') {
                    message.success(result.message || '连接测试成功！');
                } else {
                    message.error(result.message || '连接测试失败！');
                }
            } catch (error) {
                console.error('API错误:', error);
                message.error('连接测试失败: 服务器错误');
            } finally {
                setTestLoading(false);
            }
        } catch (error) {
            // 表单验证失败
            message.error('请填写必要的连接信息');
        }
    };

    // 提交表单
    const handleSubmit = async () => {
        try {
            const values = await form.validateFields();
            onSave(values as DataSource);
        } catch (error) {
            console.error('表单验证失败:', error);
        }
    };

    // 根据数据源类型渲染不同的表单字段
    const renderConnectionFields = () => {
        switch (selectedType) {
            case DataSourceType.MYSQL:
            case DataSourceType.POSTGRESQL:
            case DataSourceType.ORACLE:
            case DataSourceType.SQLSERVER:
                return (
                    <>
                        <Form.Item 
                            name="host" 
                            label="主机" 
                            rules={[{ required: true, message: '请输入主机地址' }]}
                        >
                            <Input placeholder="例如：localhost 或 192.168.1.10" />
                        </Form.Item>
                        <Form.Item 
                            name="port" 
                            label="端口" 
                            rules={[{ required: true, message: '请输入端口' }]}
                        >
                            <InputNumber 
                                style={{ width: '100%' }} 
                                min={1} 
                                max={65535} 
                                placeholder={
                                    selectedType === DataSourceType.MYSQL ? '3306' :
                                    selectedType === DataSourceType.POSTGRESQL ? '5432' :
                                    selectedType === DataSourceType.ORACLE ? '1521' :
                                    selectedType === DataSourceType.SQLSERVER ? '1433' : ''
                                }
                            />
                        </Form.Item>
                        <Form.Item 
                            name="database" 
                            label="数据库名" 
                            rules={[{ required: true, message: '请输入数据库名' }]}
                        >
                            <Input placeholder="填写要连接的数据库名称" />
                        </Form.Item>
                        <Form.Item 
                            name="username" 
                            label="用户名" 
                            rules={[{ required: true, message: '请输入用户名' }]}
                        >
                            <Input placeholder="数据库用户名" />
                        </Form.Item>
                        <Form.Item 
                            name="password" 
                            label="密码" 
                            rules={[{ required: true, message: '请输入密码' }]}
                        >
                            <Input.Password placeholder="数据库密码" />
                        </Form.Item>
                    </>
                );
            case DataSourceType.CSV:
            case DataSourceType.EXCEL:
                return (
                    <Form.Item
                        name="filePath"
                        label="文件路径"
                        rules={[{ required: true, message: '请输入文件路径' }]}
                    >
                        <Input 
                            placeholder={`例如: /path/to/file.${selectedType.toLowerCase()}`} 
                            addonAfter={<Button size="small">选择文件</Button>}
                        />
                    </Form.Item>
                );
            case DataSourceType.JSON:
                return (
                    <Form.Item
                        name="jsonContent"
                        label="JSON内容"
                        rules={[{ required: true, message: '请输入JSON内容' }]}
                    >
                        <Input.TextArea rows={6} placeholder="输入或粘贴JSON内容" />
                    </Form.Item>
                );
            default:
                return null;
        }
    };

    const title = dataSource ? '编辑数据源' : '新建数据源';

    return (
        <Modal
            title={title}
            open={visible}
            onCancel={onCancel}
            width={600}
            footer={[
                <Button key="cancel" onClick={onCancel}>
                    取消
                </Button>,
                <Button
                    key="test"
                    type="default"
                    icon={<PlayCircleOutlined />}
                    loading={testLoading}
                    onClick={handleTestConnection}
                >
                    测试连接
                </Button>,
                <Button key="submit" type="primary" onClick={handleSubmit}>
                    保存
                </Button>,
            ]}
        >
            <Form
                form={form}
                layout="vertical"
                initialValues={dataSource || { type: DataSourceType.MYSQL }}
            >
                <Form.Item
                    name="name"
                    label="数据源名称"
                    rules={[{ required: true, message: '请输入数据源名称' }]}
                >
                    <Input placeholder="数据源名称，如「生产环境MySQL」" />
                </Form.Item>

                <Form.Item
                    name="type"
                    label="数据源类型"
                    rules={[{ required: true, message: '请选择数据源类型' }]}
                >
                    <Select onChange={(value) => setSelectedType(value as DataSourceType)}>
                        <Option value={DataSourceType.MYSQL}>MySQL</Option>
                        <Option value={DataSourceType.POSTGRESQL}>PostgreSQL</Option>
                        <Option value={DataSourceType.ORACLE}>Oracle</Option>
                        <Option value={DataSourceType.SQLSERVER}>SQL Server</Option>
                        <Option value={DataSourceType.CSV}>CSV文件</Option>
                        <Option value={DataSourceType.EXCEL}>Excel文件</Option>
                        <Option value={DataSourceType.JSON}>JSON</Option>
                    </Select>
                </Form.Item>

                <Divider orientation="left">连接信息</Divider>

                {renderConnectionFields()}

                <Form.Item name="description" label="描述">
                    <Input.TextArea rows={3} placeholder="可选：添加对此数据源的描述" />
                </Form.Item>
            </Form>
        </Modal>
    );
};

export default DataSourceFormModal; 