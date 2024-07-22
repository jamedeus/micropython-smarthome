import React, { useContext } from 'react';
import ErrorModal from 'modals/ErrorModal';
import DebugModal from './DebugModal';
import ApiTargetRuleModal from 'modals/ApiTargetRuleModal';
import ScheduleToggleModal from './ScheduleToggleModal';
import Header from './Header';
import Layout from './Layout';
import FadeModal from './FadeModal';
import SaveRulesToast from './SaveRulesToast';
import { UpdateStatus } from './UpdateStatus';
import { ApiCardContext } from 'root/ApiCardContext';

const App = () => {
    const { recording } = useContext(ApiCardContext);

    return (
        <div>
            <Header />
            <Layout />
            {/* Mount UpdateStatus utility component unless recording macro */}
            {/* Status updates undo user changes while recording, confusing */}
            {recording ? null : <UpdateStatus /> }

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
