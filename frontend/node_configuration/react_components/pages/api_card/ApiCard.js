import React from 'react';
import { ErrorModal } from 'modals/ErrorModal';
import { DebugModal } from 'modals/DebugModal';
import { ScheduleToggleModal } from 'modals/ScheduleToggleModal';
import Header from './Header';
import Layout from './Layout';
import { UpdateStatus } from './UpdateStatus';
import { FadeModal } from 'modals/FadeModal';
import 'css/api_card.css';


const App = () => {
    return (
        <div className="fade-in">
            <Header />
            <Layout />
            <UpdateStatus />

            {/* Modals (hidden) */}
            <FadeModal />
            <ErrorModal />
            <DebugModal />
            <ScheduleToggleModal />
        </div>
    );
};


export default App;
