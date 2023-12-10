import React, { useContext } from 'react';
import Button from 'react-bootstrap/Button';
import { ApiOverviewContext } from 'root/ApiOverviewContext';
import { ErrorModal } from 'modals/ErrorModal';
import { ModalContextProvider } from 'modals/ModalContextProvider';
import { EditMacroModal, EditMacroModalContextProvider } from 'modals/EditMacroModal';
import Header from './Header';
import Floors from './Floors';
import Macros from './Macros';
import { LoadingSpinner } from 'util/animations';


// CSS for full-screen overlay (background behind loading spinner)
// Shown while waiting for status object after user clicks node button
const overlayStyle = `
#loading_overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 999;
}`;


const App = () => {
    // Get state bool for loading overlay
    const { loading } = useContext(ApiOverviewContext);

    const configuration = () => {
        window.location.href = "/config_overview";
    };

    return (
        <ModalContextProvider>
            <EditMacroModalContextProvider>
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
                <style>{overlayStyle}</style>
                <div id="loading_overlay" className={loading ? "d-flex" : "d-none"}>
                    <LoadingSpinner size="large" />
                </div>
            </EditMacroModalContextProvider>
        </ModalContextProvider>
    );
};


export default App;
