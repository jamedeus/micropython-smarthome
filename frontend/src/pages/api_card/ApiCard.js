import React from 'react';
import ErrorModal from 'modals/ErrorModal';
import DebugModal from './DebugModal';
import ApiTargetRuleModal from 'modals/ApiTargetRuleModal';
import ScheduleToggleModal from './ScheduleToggleModal';
import Header from './Header';
import Layout from './Layout';
import FadeModal from './FadeModal';
import SaveRulesToast from './SaveRulesToast';
import { UpdateStatus } from './UpdateStatus';

const App = () => {
    return (
        <div>
            <Header />
            <Layout />
            <UpdateStatus />

            {/* Modals (hidden) */}
            <FadeModal />
            <ErrorModal />
            <DebugModal />
            <ScheduleToggleModal />
            <ApiTargetRuleModal />
            <SaveRulesToast />
        </div>
    );
};

export default App;
