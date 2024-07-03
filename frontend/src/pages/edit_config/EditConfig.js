import React from 'react';
import PageContainer from './PageContainer';
import { ErrorModalContextProvider } from 'modals/ErrorModal';


const App = () => {
    return (
        <div>
            <ErrorModalContextProvider>
                <PageContainer />
            </ErrorModalContextProvider>
        </div>
    );
};


export default App;
