import React, { useContext } from 'react';
import Button from 'react-bootstrap/Button';
import { ApiOverviewContext } from 'root/ApiOverviewContext';
import { ErrorModal } from 'modals/ErrorModal';
import { EditMacroModal } from 'modals/EditMacroModal';
import Header from './Header';
import Floors from './Floors';
import Macros from './Macros';
import { LoadingSpinner } from 'util/animations';
import 'css/loadingOverlay.css';

const App = () => {
    // Get state bool for loading overlay
    const { loading } = useContext(ApiOverviewContext);

    const configuration = () => {
        window.location.href = "/config_overview";
    };

    return (
        <>
            <div className="d-flex flex-column vh-100">
                <Header />
                <Floors />
                <h1 className="text-center mt-5">Macros</h1>
                <Macros />

                {/* Button redirects to Node configuration overview */}
                <div className="d-flex align-items-center flex-column mt-auto py-4">
                    <Button variant="secondary" onClick={configuration}>
                        Manage
                    </Button>
                </div>

                {/* Modals (hidden) */}
                <ErrorModal />
                <EditMacroModal />
            </div>

            {/* Loading overlay (hidden) */}
            <div id="loading_overlay" className={loading ? "d-flex" : "d-none"}>
                <LoadingSpinner size="large" />
            </div>
        </>
    );
};

export default App;
