import React, { useContext } from 'react';
import ErrorModal from 'modals/ErrorModal';
import DebugModal from './DebugModal';
import ApiTargetRuleModal from 'modals/ApiTargetRuleModal';
import ScheduleToggleModal from './ScheduleToggleModal';
import Header from './Header';
import Layout from './Layout';
import LayoutEmpty from './LayoutEmpty';
import LogModal from './LogModal';
import FadeModal from './FadeModal';
import ErrorToast from 'util/ErrorToast';
import SaveRulesToast from './SaveRulesToast';
import { UpdateStatus } from './UpdateStatus';
import { ApiCardContext } from 'root/ApiCardContext';

// Returns true if object has no keys, false if has keys
const objectIsEmpty = (obj) => {
    for (let _ in obj) return false;
    return true;
};

// Returns true if status object has no devices, sensors, or ir_blaster
const statusIsEmpty = (status) => {
    return objectIsEmpty(status.devices)
        && objectIsEmpty(status.sensors)
        && !status.metadata.ir_blaster;
};

const App = () => {
    const { status, recording } = useContext(ApiCardContext);

    return (
        <div className="h-100">
            <Header />
            {/* Show help message and link to edit config if status empty */}
            {statusIsEmpty(status) ? (
                <LayoutEmpty />
            ) : (
                <Layout />
            )}
            {/* Mount UpdateStatus utility component unless recording macro */}
            {/* Status updates undo user changes while recording, confusing */}
            {recording ? null : <UpdateStatus /> }

            {/* Modals (hidden) */}
            <LogModal />
            <FadeModal />
            <ErrorModal />
            <DebugModal />
            <ScheduleToggleModal />
            <ApiTargetRuleModal />
            <SaveRulesToast />
            <ErrorToast />
        </div>
    );
};

export default App;
