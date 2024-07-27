import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './Offline';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'spinkit/spinkit.min.css';
import 'css/dark_mode.scss';
import 'css/style.css';

const container = document.getElementById('root');
const root = createRoot(container);
root.render(<App />);
