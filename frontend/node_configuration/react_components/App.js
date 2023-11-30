import React from 'react';
import PageContainer from './PageContainer';
import { UploadModalContextProvider } from './UploadModal';


const App = () => {
    return (
        <div>
            <UploadModalContextProvider>
                <PageContainer />
            </UploadModalContextProvider>
        </div>
    );
};


export default App;
