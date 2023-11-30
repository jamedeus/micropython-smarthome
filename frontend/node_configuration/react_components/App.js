import React from 'react';
import PageContainer from './PageContainer';
import { ErrorModalContextProvider } from './ErrorModal';
import { UploadModalContextProvider } from './UploadModal';


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
