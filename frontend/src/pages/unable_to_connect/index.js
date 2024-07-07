import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './UnableToConnect';
import 'css/dark_mode.scss';
import 'css/style.css';

const container = document.getElementById('root');
const root = createRoot(container);
root.render(<App />);
