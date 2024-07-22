import React from 'react';
import { createRoot } from 'react-dom/client';
import { ConfigProvider } from 'root/ConfigContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import EditConfig from './EditConfig';
import 'bootstrap/dist/js/bootstrap.min.js';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import 'spinkit/spinkit.min.css';
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
