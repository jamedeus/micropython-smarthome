import React, { useState, createContext } from 'react';
import PropTypes from 'prop-types';
import Cookies from 'js-cookie';
import { showErrorToast } from 'util/ErrorToast';
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
        const response = await fetch(`/delete_macro/${name}`);

        // Remove from state if successful
        if (response.ok) {
            const update = { ...macros };
            delete update[name];
            setMacros(update);
            return true;
        } else {
            showErrorToast('Failed to delete macro');
            return false;
        }
    };

    const deleteMacroAction = async (name, index) => {
        // Delete macro action
        const response = await fetch(`/delete_macro_action/${name}/${index}`);

        // Remove action from state if successful
        if (response.ok) {
            const update = { ...macros,
                [name]: macros[name].filter((_, idx) => idx !== index)
            };
            setMacros(update);

            // If last action deleted remove whole macro
            if (!update[name].length) {
                deleteMacro(name);
            }
        } else {
            showErrorToast('Failed to delete macro action');
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
    const finishRecording = async () => {
        // Get full macro actions from backend (this is in django context, but
        // if user pressed back after adding action it will be outdated)
        const response = await fetch(`/get_macro_actions/${recording}`);
        if (response.ok) {
            const data = await response.json();
            setMacros({ ...macros, [recording]: data.message });
        }
        setRecording('');
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
