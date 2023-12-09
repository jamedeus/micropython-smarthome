import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './ApiOverview';
import { ApiOverviewContextProvider } from 'root/ApiOverviewContext';
import 'root/style.scss';


const container = document.getElementById('root');
const root = createRoot(container);
root.render(
    <ApiOverviewContextProvider>
        <App />
    </ApiOverviewContextProvider>
);
