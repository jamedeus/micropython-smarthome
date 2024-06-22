import React from 'react';
import PageContainer from 'layout/PageContainer';
import { ErrorModalContextProvider } from 'modals/ErrorModal';
import { UploadModalContextProvider } from 'modals/UploadModal';


const App = () => {
    return (
        <div>
            <UploadModalContextProvider>
                <ErrorModalContextProvider>
                    <PageContainer />
                </ErrorModalContextProvider>
            </UploadModalContextProvider>
        </div>
    );
};


export default App;
