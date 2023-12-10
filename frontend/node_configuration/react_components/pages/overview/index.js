import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './Overview';
import { OverviewContextProvider } from 'root/OverviewContext';
import 'css/dark_mode.scss';


const container = document.getElementById('root');
const root = createRoot(container);
root.render(
    <OverviewContextProvider>
        <App />
    </OverviewContextProvider>
);
