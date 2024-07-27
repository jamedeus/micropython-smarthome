import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './ApiOverview';
import { ApiOverviewContextProvider } from 'root/ApiOverviewContext';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import 'spinkit/spinkit.min.css';
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
