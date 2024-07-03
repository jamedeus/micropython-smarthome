import React, { useContext } from 'react';
import Button from 'react-bootstrap/Button';
import { OverviewContext } from 'root/OverviewContext';
import Header from './Header';
import KeywordsTable from './KeywordsTable';
import NewConfigTable from './NewConfigTable';
import ExistingNodesTable from './ExistingNodesTable';
import { ErrorModal } from 'modals/ErrorModal';
import UploadModal from 'modals/UploadModal';
import { ChangeIpModal } from 'modals/ChangeIpModal';
import { ModalContextProvider } from 'modals/ModalContextProvider';


const App = () => {
    // Get django context
    const { context } = useContext(OverviewContext);

    const new_config = () => {
        window.location.href = "new_config";
    };

    const frontend = () => {
        window.location.href = "/api";
    };

    return (
        <ModalContextProvider>
            <div className="d-flex flex-column vh-100">
                <Header />

                {/* Add new config table if un-uploaded configs exist */}
                {context.not_uploaded.length ? <NewConfigTable /> : null}

                {/* Add existing nodes table if existing nodes exist */}
                {context.uploaded.length ? <ExistingNodesTable /> : null}

                {/* Button to create new config file */}
                <div className="mt-2 mb-5 text-center">
                    <Button variant="primary" onClick={new_config}>
                        Create new config
                    </Button>
                </div>

                {/* Add schedule keywords table */}
                <KeywordsTable />

                {/* Button redirects to API frontend */}
                <div className="d-flex align-items-center flex-column mt-auto py-4">
                    <Button variant="secondary" onClick={frontend}>
                        Frontend
                    </Button>
                </div>

                {/* Modals (hidden) */}
                <UploadModal />
                <ErrorModal />
                <ChangeIpModal />
            </div>
        </ModalContextProvider>
    );
};


export default App;
