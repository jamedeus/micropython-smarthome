import React, { useContext, useEffect } from 'react';
import { ConfigContext } from './ConfigContext';
import Page1 from './Page1';


const App = () => {
    const { config, updateConfig } = useContext(ConfigContext);

    // Logic to determine which page to show
    // For simplicity, showing PageOne
    return (
        <div>
        <Page1 />
        </div>
    );
};


export default App;
