import React, { useState, createContext } from 'react';
import PropTypes from 'prop-types';


export const OverviewContext = createContext();

export const OverviewContextProvider = ({ children }) => {
    // Load context set by django template
    const [context, setContext] = useState(() => {
        function parse_dom_context(name) {
            const element = document.getElementById(name);
            return JSON.parse(element.textContent);
        }

        // Parse context elements created by django template
        return {
            not_uploaded: parse_dom_context("not_uploaded"),
            uploaded: parse_dom_context("uploaded"),
            schedule_keywords: parse_dom_context("schedule_keywords"),
            client_ip: parse_dom_context("client_ip")
        };
    });

    return (
        <OverviewContext.Provider value={{ context, setContext }}>
            {children}
        </OverviewContext.Provider>
    );
};

OverviewContextProvider.propTypes = {
    children: PropTypes.node,
};
