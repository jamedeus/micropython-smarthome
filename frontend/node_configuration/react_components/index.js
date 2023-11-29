import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { ConfigProvider } from './ConfigContext';
import './../style.scss';


const container = document.getElementById('root');
const root = createRoot(container);
root.render(
    <ConfigProvider>
        <App />
    </ConfigProvider>
);
