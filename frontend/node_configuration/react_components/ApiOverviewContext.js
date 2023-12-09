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

    const deleteMacro = (name) => {
        let update = { ...context.macros };
        delete update[name];
        setContext({ ...context, ["macros"]: update});
    };

    return (
        <ApiOverviewContext.Provider value={{ context, setContext, deleteMacro }}>
            {children}
        </ApiOverviewContext.Provider>
    );
};

ApiOverviewContextProvider.propTypes = {
    children: PropTypes.node,
};
