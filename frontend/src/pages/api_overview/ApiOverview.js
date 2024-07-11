import React, { useContext } from 'react';
import Button from 'react-bootstrap/Button';
import { ApiOverviewContext } from 'root/ApiOverviewContext';
import ErrorModal from 'modals/ErrorModal';
import EditMacroModal from './EditMacroModal';
import RecordMacroModal from './RecordMacroModal';
import Header from './Header';
import Floors from './Floors';
import Macros, { FinishRecordingButton } from './Macros';
import { LoadingSpinner } from 'util/animations';
import 'css/loadingOverlay.css';

const App = () => {
    // Get state bools for loading overlay, macro recording mode
    const { loading, recording } = useContext(ApiOverviewContext);

    const configuration = () => {
        window.location.href = "/config_overview";
    };

    return (
        <>
            <div className="d-flex flex-column vh-100">
                <Header />
                <Floors />
                <h1 className="text-center mt-5">
                    Macros
                </h1>
                {recording ? <FinishRecordingButton /> : <Macros />}

                {/* Button redirects to Node configuration overview */}
                <div className="d-flex mx-auto flex-column mt-auto py-4">
                    <Button variant="secondary" onClick={configuration}>
                        Manage
                    </Button>
                </div>

                {/* Modals (hidden) */}
                <ErrorModal />
                <EditMacroModal />
                <RecordMacroModal />
            </div>

            {/* Loading overlay (shown after clicking node button) */}
            {loading ? (
                <div id="loading_overlay">
                    <LoadingSpinner size="large" />
                </div>
            ) : null}
        </>
    );
};

export default App;
