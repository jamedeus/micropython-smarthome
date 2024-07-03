import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './Overview';
import { ErrorModalContextProvider } from 'modals/ErrorModal';
import { OverviewContextProvider } from 'root/OverviewContext';
import 'css/dark_mode.scss';
import 'css/style.css';


const container = document.getElementById('root');
const root = createRoot(container);
root.render(
    <ErrorModalContextProvider>
        <OverviewContextProvider>
            <App />
        </OverviewContextProvider>
    </ErrorModalContextProvider>
);
