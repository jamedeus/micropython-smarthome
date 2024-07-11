import React, { useState, createContext } from 'react';
import PropTypes from 'prop-types';
import { parse_dom_context } from 'util/django_util';

export const ApiOverviewContext = createContext();

export const ApiOverviewContextProvider = ({ children }) => {
    // Load context set by django template
    const [context, setContext] = useState(() => {
        return {
            macros: parse_dom_context("macros"),
            start_recording: false
        };
    });

    // Create state for macro record mode, contains name of macro
    // being recorded (default loaded from django template context)
    const [recording, setRecording] = useState(() => {
        return parse_dom_context("recording");
    });

    // Create state to show loading overlay
    const [loading, setLoading] = useState(false);

    // Remove loading overlay when navigated to with browser back button
    window.onpageshow = function(event) {
        if (event.persisted) {
            setLoading(false);
        }
    };

    const deleteMacro = async (name) => {
        // Delete macro
        const result = await fetch(`/delete_macro/${name}`);

        // Remove from state if successful
        if (result.ok) {
            const update = { ...context.macros };
            delete update[name];
            setContext({ ...context, macros: update });
        } else {
            // TODO improve failure handling
            alert('Failed to delete macro');
        }
    };

    const deleteMacroAction = async (name, index) => {
        // Delete macro action
        const result = await fetch(`/delete_macro_action/${name}/${index}`);

        // Remove action from state if successful
        if (result.ok) {
            const update = { ...context.macros,
                [name]: context.macros[name].filter((_, idx) => idx !== index)
            };
            setContext({ ...context, macros: update });

            // If last action deleted remove whole macro
            if (!update[name].length) {
                deleteMacro(name);
            }
        } else {
            // TODO improve failure handling
            alert('Failed to delete macro action');
        }
    };

    // Takes new macro name, sets recording state, sets context param
    // that opens instruction modal if "don't show again" cookie not set
    const startRecording = (name) => {
        setRecording(name);
        setContext({ ...context, start_recording: true});
    };

    return (
        <ApiOverviewContext.Provider value={{
            context,
            setContext,
            recording,
            setRecording,
            loading,
            setLoading,
            deleteMacro,
            deleteMacroAction,
            startRecording
        }}>
            {children}
        </ApiOverviewContext.Provider>
    );
};

ApiOverviewContextProvider.propTypes = {
    children: PropTypes.node,
};
