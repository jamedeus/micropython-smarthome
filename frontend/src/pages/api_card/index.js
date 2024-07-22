import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './ApiCard';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import { MetadataContextProvider } from 'root/MetadataContext';
import 'bootstrap/dist/js/bootstrap.bundle.min';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import 'spinkit/spinkit.min.css';
import 'css/dark_mode.scss';
import 'css/api_card.css';
import 'css/macros.css';
import 'css/style.css';

const container = document.getElementById('root');
const root = createRoot(container);
root.render(
    <MetadataContextProvider>
        <ApiCardContextProvider>
            <App />
        </ApiCardContextProvider>
    </MetadataContextProvider>
);
