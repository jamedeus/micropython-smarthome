import React from 'react';
import { ErrorModal } from 'modals/ErrorModal';
import { DebugModal } from 'modals/DebugModal';
import Header from './Header';
import Layout from './Layout';
import { UpdateStatus } from './UpdateStatus';
import 'css/api_card.css';


const App = () => {
    return (
        <div className="fade-in">
            <Header />
            <Layout />
            <UpdateStatus />

            {/* Modals (hidden) */}
            <ErrorModal />
            <DebugModal />
        </div>
    );
};


export default App;
