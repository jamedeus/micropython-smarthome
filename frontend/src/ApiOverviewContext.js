import React, { useState, createContext } from 'react';
import PropTypes from 'prop-types';
import { parse_dom_context } from 'util/django_util';

export const ApiOverviewContext = createContext();

export const ApiOverviewContextProvider = ({ children }) => {
    // Load context set by django template
    const [context, setContext] = useState(() => {
        return {
            nodes: parse_dom_context("nodes"),
            macros: parse_dom_context("macros"),
            recording: parse_dom_context("recording"),
            start_recording: false
        };
    });

    // Create state for macro record mode, contains name of macro
    // being recorded (default loaded from django template context)
    const [recording, setRecording] = useState(context.recording);

    // Create state to show loading overlay
    const [loading, setLoading] = useState(false);

    // Remove loading overlay when navigated to with browser back button
    window.onpageshow = function(event) {
        if (event.persisted) {
            setLoading(false);
        }
    };

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

    // Takes new macro name, sets recording state, sets context param
    // that opens instruction modal if "don't show again" cookie not set
    const startRecording = (name) => {
        setRecording(name);
        setContext({ ...context, ["start_recording"]: true});
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
