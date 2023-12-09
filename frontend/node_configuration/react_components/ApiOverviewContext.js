import React, { useState, createContext } from 'react';
import PropTypes from 'prop-types';


export const ApiOverviewContext = createContext();

export const ApiOverviewContextProvider = ({ children }) => {
    // Load context set by django template
    const [context, setContext] = useState(() => {
        function parse_dom_context(name) {
            const element = document.getElementById(name);
            if (element) {
                return JSON.parse(element.textContent);
            } else {
                return "";
            }
        }

        // Parse context elements created by django template
        return {
            nodes: parse_dom_context("nodes"),
            macros: parse_dom_context("macros"),
            recording: parse_dom_context("recording")
        };
    });

    // Create state for macro record mode, contains name of macro
    // being recorded (default loaded from django template context)
    const [recording, setRecording] = useState(context.recording);

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
