import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './ApiOverview';
import { ApiOverviewContextProvider } from 'root/ApiOverviewContext';
import { EditMacroModalContextProvider } from 'modals/EditMacroModal';
import 'css/dark_mode.scss';
import 'css/style.css';

const container = document.getElementById('root');
const root = createRoot(container);
root.render(
    <ApiOverviewContextProvider>
        <EditMacroModalContextProvider>
            <App />
        </EditMacroModalContextProvider>
    </ApiOverviewContextProvider>
);
