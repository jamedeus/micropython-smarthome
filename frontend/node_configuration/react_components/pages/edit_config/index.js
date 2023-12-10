import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './EditConfig';
import { ConfigProvider } from 'root/ConfigContext';
import 'css/dark_mode.scss';


const container = document.getElementById('root');
const root = createRoot(container);
root.render(
    <ConfigProvider>
        <App />
    </ConfigProvider>
);
