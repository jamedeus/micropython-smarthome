import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './ApiCard';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import 'css/dark_mode.scss';
import 'css/api_card.css';
import 'css/macros.css';
import 'css/style.css';

const container = document.getElementById('root');
const root = createRoot(container);
root.render(
    <ApiCardContextProvider>
        <App />
    </ApiCardContextProvider>
);
