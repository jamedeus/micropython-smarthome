import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './ApiOverview';
import { ApiOverviewContextProvider } from 'root/ApiOverviewContext';
import 'css/dark_mode.scss';
import 'css/style.css';
import 'css/macros.css';

const container = document.getElementById('root');
const root = createRoot(container);
root.render(
    <ApiOverviewContextProvider>
        <App />
    </ApiOverviewContextProvider>
);
