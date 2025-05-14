import React from 'react';
import { ConfigProvider, App as AntApp } from 'antd'; // AntApp is for context methods like message, notification
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout'; // Import the new layout
import KGVisualizationPage from './features/kgVisualization/KGVisualizationPage'; // Uncommented
import DataSourcesPage from './features/dataSources/DataSourcesPage'; // Import the actual DataSourcesPage
import DataModelingPage from './features/dataModeling'; // Import the new DataModelingPage
import './App.css'; // Assuming you have App.css for global app styles

// Placeholder for KGVisualizationPage until we create it - REMOVE THIS or keep for other tests
// const KGVisualizationPagePlaceholder = () => (
//   <div>
//     <h2>Knowledge Graph Visualization Page (Placeholder)</h2>
//     <p>This page will display the graph visualization.</p>
//   </div>
// );

// Placeholder for other pages - you will replace these with actual components
const HomePage = () => <div style={{textAlign: 'center', paddingTop: '50px'}}><h2>仪表盘 / 首页</h2><p>欢迎使用知识图谱与智能问答系统！</p></div>;
const KGPipelinesPage = () => <div style={{textAlign: 'center', paddingTop: '50px'}}><h2>知识图谱构建流程页</h2></div>;
const NL2SQLPage = () => <div style={{textAlign: 'center', paddingTop: '50px'}}><h2>智能问答页</h2></div>;
const ProfilePage = () => <div style={{textAlign: 'center', paddingTop: '50px'}}><h2>个人中心页</h2></div>;
const SettingsPage = () => <div style={{textAlign: 'center', paddingTop: '50px'}}><h2>设置页</h2></div>;

// Placeholder for a simple Login page (outside MainLayout)
const LoginPage = () => (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <h2>登录页 (占位)</h2>
        {/* TODO: Add login form */}
        <p><a href="/">进入系统 (临时)</a></p> 
    </div>
);

// Simulate auth status - replace with actual auth logic from Redux/Context
const isAuthenticated = true; // TODO: Replace with actual authentication check

function App() {
  return (
    <ConfigProvider
      theme={{
        // Customize Ant Design theme here if needed
        // token: {
        //   colorPrimary: '#00b96b',
        // },
      }}
    >
      <AntApp> {/* Wrapper for Ant Design context-based components like message, notification, modal */}
        <Router>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            {
              isAuthenticated ? (
                <Route path="/*" element={<MainLayout />}> {/* All main app routes go through MainLayout */}
                  <Route index element={<HomePage />} /> {/* Default route for / shows HomePage */}
                  <Route path="kg-visualization" element={<KGVisualizationPage />} />
                  <Route path="data-sources" element={<DataSourcesPage />} />
                  <Route path="data-modeling" element={<DataModelingPage />} />
                  <Route path="kg-pipelines" element={<KGPipelinesPage />} />
                  <Route path="nl2sql" element={<NL2SQLPage />} />
                  <Route path="profile" element={<ProfilePage />} />
                  <Route path="settings" element={<SettingsPage />} />
                  {/* Add other nested routes for MainLayout here */}
                  <Route path="*" element={<Navigate to="/" replace />} /> {/* Fallback for unknown routes under MainLayout */}
                </Route>
              ) : (
                <Route path="*" element={<Navigate to="/login" replace />} />
              )
            }
          </Routes>
        </Router>
      </AntApp>
    </ConfigProvider>
  );
}

export default App; 