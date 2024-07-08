import React, { useContext } from 'react';
import ErrorModal from 'modals/ErrorModal';
import DebugModal from 'modals/DebugModal';
import ApiTargetRuleModal from 'modals/ApiTargetRuleModal';
import ScheduleToggleModal from 'modals/ScheduleToggleModal';
import Header from './Header';
import Layout from './Layout';
import FadeModal from 'modals/FadeModal';
import { UpdateStatus } from './UpdateStatus';
import { ApiCardContext } from 'root/ApiCardContext';
import 'css/api_card.css';


const App = () => {
    // Get state bool for loading animation
    const { loading } = useContext(ApiCardContext);

    return (
        <div className={loading ? "fade-in" : "fade-out"}>
            <Header />
            <Layout />
            <UpdateStatus />

            {/* Modals (hidden) */}
            <FadeModal />
            <ErrorModal />
            <DebugModal />
            <ScheduleToggleModal />
            <ApiTargetRuleModal />
        </div>
    );
};


export default App;
