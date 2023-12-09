import React, { useState, createContext } from 'react';
import PropTypes from 'prop-types';


export const ApiOverviewContext = createContext();

export const ApiOverviewContextProvider = ({ children }) => {
    // Load context set by django template
    const [context, setContext] = useState(() => {
        function parse_dom_context(name) {
            const element = document.getElementById(name);
            return JSON.parse(element.textContent);
        }

        // Parse context elements created by django template
        return {
            nodes: parse_dom_context("nodes"),
            macros: parse_dom_context("macros")
        };
    });

    // Create state for macro record mode
    const [recording, setRecording] = useState("");

    const deleteMacro = (name) => {
        let update = { ...context.macros };
        delete update[name];
        setContext({ ...context, ["macros"]: update});
    };

    const deleteMacroAction = (name, index) => {
        let update = { ...context.macros };
        delete update[name][index];
        // If last action deleted remove whole macro
        if (update[name].every(item => item === null)) {
            deleteMacro(name);
        // If actions remain update macro
        } else {
            setContext({ ...context, ["macros"]: update});
        }
    };

    return (
        <ApiOverviewContext.Provider value={{
            context,
            setContext,
            recording,
            setRecording,
            deleteMacro,
            deleteMacroAction
        }}>
            {children}
        </ApiOverviewContext.Provider>
    );
};

ApiOverviewContextProvider.propTypes = {
    children: PropTypes.node,
};
