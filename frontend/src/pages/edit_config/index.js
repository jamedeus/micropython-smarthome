import React from 'react';
import { createRoot } from 'react-dom/client';
import { ConfigProvider } from 'root/ConfigContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import EditConfig from './EditConfig';
import 'css/edit_config.css';
import 'css/dark_mode.scss';
import 'css/style.css';

const container = document.getElementById('root');
const root = createRoot(container);
root.render(
    <MetadataContextProvider>
        <ConfigProvider>
            <EditConfig />
        </ConfigProvider>
    </MetadataContextProvider>
);
