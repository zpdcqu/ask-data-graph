import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css'; // Assuming you have a global stylesheet
import { Provider } from 'react-redux';
import { store } from './store';

// Import Ant Design CSS globally if you haven't elsewhere (e.g., in App.tsx)
// import 'antd/dist/reset.css'; // Modern Ant Design reset (or antd/dist/antd.css for older versions)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </React.StrictMode>,
); 