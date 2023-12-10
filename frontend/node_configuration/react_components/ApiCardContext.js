import React, { useState, createContext } from 'react';
import PropTypes from 'prop-types';


export const ApiCardContext = createContext();

export const ApiCardContextProvider = ({ children }) => {
    // Load context set by django template
    const [status, setStatus] = useState(() => {
        function parse_dom_context(name) {
            const element = document.getElementById(name);
            if (element) {
                return JSON.parse(element.textContent);
            } else {
                return "";
            }
        }

        // Parse context element created by django template
        return parse_dom_context("context");
    });

    return (
        <ApiCardContext.Provider value={{
            status,
            setStatus
        }}>
            {children}
        </ApiCardContext.Provider>
    );
};

ApiCardContextProvider.propTypes = {
    children: PropTypes.node,
};
