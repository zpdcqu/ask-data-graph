import React, { useState } from 'react';
import { Layout, Menu, Typography, Avatar, Dropdown, Space, Breadcrumb, Row, Col } from 'antd';
import {
    DesktopOutlined,
    PieChartOutlined,
    FileOutlined,
    TeamOutlined,
    UserOutlined,
    ShareAltOutlined, // For KG Visualization
    DatabaseOutlined, // For Data Sources
    SlidersOutlined,  // For KG Pipelines
    ApartmentOutlined, // For KG Tasks
    PlayCircleOutlined, // For KG Runs
    QuestionCircleOutlined, // For NL2SQL
    SettingOutlined, // For Settings
    LogoutOutlined, // For Logout
    HomeOutlined, // For Home/Dashboard
} from '@ant-design/icons';
import { Link, useLocation, Outlet } from 'react-router-dom'; // Outlet for nested routes

const { Header, Content, Footer, Sider } = Layout;
const { Title } = Typography;

interface MenuItem {
    key: string;
    icon?: React.ReactNode;
    label: React.ReactNode;
    path?: string;
    children?: MenuItem[];
}

const menuItems: MenuItem[] = [
    { key: 'dashboard', label: '仪表盘', icon: <HomeOutlined />, path: '/' },
    {
        key: 'kg', 
        label: '知识图谱', 
        icon: <ShareAltOutlined />,
        children: [
            { key: 'kg-visualization', label: '图谱可视化', icon: <ShareAltOutlined />, path: '/kg-visualization' },
            { key: 'kg-pipelines', label: '构建流程', icon: <SlidersOutlined />, path: '/kg-pipelines' },
            // { key: 'kg-tasks', label: '构建任务', icon: <ApartmentOutlined />, path: '/kg-tasks' }, // Usually part of pipeline detail
            // { key: 'kg-runs', label: '运行记录', icon: <PlayCircleOutlined />, path: '/kg-runs' },
        ]
    },
    { key: 'data-sources', label: '数据源管理', icon: <DatabaseOutlined />, path: '/data-sources' },
    { key: 'nl2sql', label: '智能问答', icon: <QuestionCircleOutlined />, path: '/nl2sql' },
    // Add more top-level or nested menu items based on front_end.md
];

// Function to render menu items, handling nesting
const renderMenuItems = (items: MenuItem[]) => {
    return items.map(item => {
        if (item.children) {
            return (
                <Menu.SubMenu key={item.key} icon={item.icon} title={item.label}>
                    {renderMenuItems(item.children)}
                </Menu.SubMenu>
            );
        }
        return (
            <Menu.Item key={item.path || item.key} icon={item.icon}>
                <Link to={item.path || '#'}>{item.label}</Link>
            </Menu.Item>
        );
    });
};

// User dropdown menu
const userMenuItems = (
    <Menu>
        <Menu.Item key="profile" icon={<UserOutlined />}>
            <Link to="/profile">个人中心</Link>
        </Menu.Item>
        <Menu.Item key="settings" icon={<SettingOutlined />}>
            <Link to="/settings">设置</Link>
        </Menu.Item>
        <Menu.Divider />
        <Menu.Item key="logout" icon={<LogoutOutlined />}>
            退出登录 {/* TODO: Implement logout functionality */}
        </Menu.Item>
    </Menu>
);

const MainLayout: React.FC = () => {
    const [collapsed, setCollapsed] = useState(false);
    const location = useLocation();

    // Determine selected keys for menu based on current path
    const selectedKeys = menuItems.reduce<string[]>((acc, item) => {
        if (item.path && location.pathname.startsWith(item.path)) {
            acc.push(item.path);
        }
        if (item.children) {
            item.children.forEach(child => {
                if (child.path && location.pathname.startsWith(child.path)) {
                    acc.push(child.path);
                }
            });
        }
        return acc;
    }, []);
    
    // Determine open keys for submenus
    const openKeys = menuItems
        .filter(item => item.children && item.children.some(child => child.path && location.pathname.startsWith(child.path)))
        .map(item => item.key);


    // TODO: Replace with actual breadcrumb logic based on routes
    const breadcrumbItems = [
        { title: <Link to="/">首页</Link> },
        // Example: if location.pathname is /kg-visualization, add that
    ];
    if (location.pathname !== '/') {
        const pathParts = location.pathname.split('/').filter(p => p);
        let currentPath = '';
        pathParts.forEach(part => {
            currentPath += `/${part}`;
            const menuItem = menuItems.flatMap(item => item.children || [item]).find(item => item.path === currentPath);
            breadcrumbItems.push({
                title: menuItem ? <Link to={menuItem.path!}>{menuItem.label}</Link> : part
            });
        });
    }

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Sider collapsible collapsed={collapsed} onCollapse={(value) => setCollapsed(value)}>
                <div style={{
                    height: '32px',
                    margin: '16px',
                    background: 'rgba(255, 255, 255, 0.2)',
                    textAlign: 'center',
                    lineHeight: '32px',
                    color: 'white',
                    overflow: 'hidden'
                }}>
                    {collapsed ? 'KG' : '知识图谱平台'}
                </div>
                <Menu theme="dark" defaultSelectedKeys={['/']} selectedKeys={selectedKeys} defaultOpenKeys={openKeys} mode="inline">
                    {renderMenuItems(menuItems)}
                </Menu>
            </Sider>
            <Layout className="site-layout">
                <Header className="site-layout-background" style={{ padding: '0 16px', background: '#fff' }}>
                    <Row justify="space-between" align="middle">
                        <Col>
                            {/* Can add a menu toggle button for mobile or if Sider is not collapsible by default */}
                        </Col>
                        <Col>
                            <Dropdown overlay={userMenuItems} placement="bottomRight">
                                <a onClick={e => e.preventDefault()} style={{ cursor: 'pointer' }}>
                                    <Space>
                                        <Avatar size="small" icon={<UserOutlined />} />
                                        用户名 {/* Replace with actual username */}
                                    </Space>
                                </a>
                            </Dropdown>
                        </Col>
                    </Row>
                </Header>
                <Content style={{ margin: '0 16px' }}>
                    <Breadcrumb style={{ margin: '16px 0' }} items={breadcrumbItems} />
                    <div className="site-layout-background" style={{ padding: 24, minHeight: 360, background: '#fff' }}>
                        <Outlet /> {/* This is where nested routes will render their components */}
                    </div>
                </Content>
                <Footer style={{ textAlign: 'center' }}>
                    知识图谱与智能问答系统 ©{new Date().getFullYear()} Created by YourTeam
                </Footer>
            </Layout>
        </Layout>
    );
};

export default MainLayout; 