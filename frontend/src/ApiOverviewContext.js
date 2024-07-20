import React, { useState, createContext } from 'react';
import PropTypes from 'prop-types';
import Cookies from 'js-cookie';
import { parse_dom_context } from 'util/django_util';

export const ApiOverviewContext = createContext();

export const ApiOverviewContextProvider = ({ children }) => {
    // Load existing macros from context set by django template
    const [macros, setMacros] = useState(() => {
        return parse_dom_context("macros");
    });

    // Create state for name of macro being recorded from django context
    const [recording, setRecording] = useState(() => {
        return parse_dom_context("recording");
    });

    // Create state that controls instructions modal visibility
    const [showInstructions, setShowInstructions] = useState(false);

    // Create state to show loading overlay
    const [loading, setLoading] = useState(false);

    // Remove loading overlay when navigated to with browser back button
    window.onpageshow = function(event) {
        /* istanbul ignore else */
        if (event.persisted) {
            setLoading(false);
        }
    };

    const deleteMacro = async (name) => {
        // Delete macro
        const result = await fetch(`/delete_macro/${name}`);

        // Remove from state if successful
        if (result.ok) {
            const update = { ...macros };
            delete update[name];
            setMacros(update);
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
            const update = { ...macros,
                [name]: macros[name].filter((_, idx) => idx !== index)
            };
            setMacros(update);

            // If last action deleted remove whole macro
            if (!update[name].length) {
                deleteMacro(name);
            }
        } else {
            // TODO improve failure handling
            alert('Failed to delete macro action');
        }
    };

    // Takes new or existing macro name, sets recording state, shows
    // instructions modal if skip_instructions cookie is not set
    const startRecording = (name) => {
        setRecording(name);
        if (!Cookies.get("skip_instructions")) {
            setShowInstructions(true);
        }
    };

    // Reset state, remove name from URL (prevent resuming if page refreshed)
    const finishRecording = () => {
        setRecording("");
        history.pushState({}, '', '/api');
    };

    return (
        <ApiOverviewContext.Provider value={{
            macros,
            recording,
            showInstructions,
            loading,
            setLoading,
            deleteMacro,
            deleteMacroAction,
            startRecording,
            finishRecording
        }}>
            {children}
        </ApiOverviewContext.Provider>
    );
};

ApiOverviewContextProvider.propTypes = {
    children: PropTypes.node,
};
