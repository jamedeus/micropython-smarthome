import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './ApiCard';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import { ErrorModalContextProvider } from 'modals/ErrorModal';
import 'css/dark_mode.scss';
import 'css/style.css';


const container = document.getElementById('root');
const root = createRoot(container);
root.render(
    <ErrorModalContextProvider>
        <ApiCardContextProvider>
            <App />
        </ApiCardContextProvider>
    </ErrorModalContextProvider>
);
