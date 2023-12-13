import React from 'react';
import { ErrorModal } from 'modals/ErrorModal';
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
        </div>
    );
};


export default App;
