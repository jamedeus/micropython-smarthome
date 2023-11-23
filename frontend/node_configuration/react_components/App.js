import React, { useContext, useEffect } from 'react';
import { ConfigContext } from './ConfigContext';
import PageContainer from './PageContainer';


const App = () => {
    const { config, updateConfig } = useContext(ConfigContext);

    // Logic to determine which page to show
    // For simplicity, showing PageOne
    return (
        <div>
            <PageContainer />
        </div>
    );
};


export default App;
