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

    return (
        <ApiOverviewContext.Provider value={{ context, setContext }}>
            {children}
        </ApiOverviewContext.Provider>
    );
};

ApiOverviewContextProvider.propTypes = {
    children: PropTypes.node,
};
