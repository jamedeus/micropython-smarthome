import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './ApiCard';
import { ApiCardContextProvider } from 'root/ApiCardContext';
import { ModalContextProvider } from 'modals/ModalContextProvider';
import { ScheduleToggleContextProvider } from 'modals/ScheduleToggleModal';
import 'css/dark_mode.scss';
import 'css/style.css';


const container = document.getElementById('root');
const root = createRoot(container);
root.render(
    <ModalContextProvider>
        <ApiCardContextProvider>
            <ScheduleToggleContextProvider>
                <App />
            </ScheduleToggleContextProvider>
        </ApiCardContextProvider>
    </ModalContextProvider>
);
