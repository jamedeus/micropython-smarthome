import React from 'react';
import Button from 'react-bootstrap/Button';
import Header from './Header';
import KeywordsTable from './KeywordsTable';
import NewConfigTable from './NewConfigTable';
import ExistingNodesTable from './ExistingNodesTable';
import { ErrorModalContextProvider } from 'modals/ErrorModal';
import { UploadModalContextProvider } from 'modals/UploadModal';


const App = () => {

    const new_config = () => {
        window.location.href = "new_config"
    }

    return (
        <div className="d-flex flex-column vh-100">
            <Header />
            <NewConfigTable />
            <ExistingNodesTable />
            <div className="mt-2 mb-5 text-center">
                <Button variant="primary" onClick={new_config}>
                    Create new config
                </Button>
            </div>
            <KeywordsTable />
        </div>
    );
};


export default App;
