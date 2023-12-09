import React, { useContext } from 'react';
import Button from 'react-bootstrap/Button';
import { ApiOverviewContext } from 'root/ApiOverviewContext';
import { ErrorModal } from 'modals/ErrorModal';
import { ModalContextProvider } from 'modals/ModalContextProvider';
import Header from './Header';
import Floors from './Floors';


const App = () => {
    // Get django context
    const { context } = useContext(ApiOverviewContext);

    const configuration = () => {
        window.location.href = "/config_overview";
    };

    return (
        <ModalContextProvider>
            <div className="d-flex flex-column vh-100">
                <Header />
                <Floors />

                {/* Button redirects to Node configuration overview */}
                <div className="d-flex align-items-center flex-column mt-auto py-4">
                    <Button variant="secondary" onClick={configuration}>
                        Manage
                    </Button>
                </div>

                {/* Modals (hidden) */}
                <ErrorModal />
            </div>
        </ModalContextProvider>
    );
};


export default App;
