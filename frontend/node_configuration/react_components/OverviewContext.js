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

    const addScheduleKeyword = (keyword, timestamp) => {
        let update = { ...context.schedule_keywords };
        update[keyword] = timestamp;
        setContext({ ...context, ["schedule_keywords"]: update})
    };

    const editScheduleKeyword = (keyword_old, keyword_new, timestamp_new) => {
        let update = { ...context.schedule_keywords };
        if (keyword_old === keyword_new) {
            update[keyword_old] = timestamp_new;
        } else {
            delete update[keyword_old];
            update[keyword_new] = timestamp_new;
        }
        setContext({ ...context, ["schedule_keywords"]: update})
    };

    const deleteScheduleKeyword = (keyword) => {
        let update = { ...context.schedule_keywords };
        delete update[keyword];
        setContext({ ...context, ["schedule_keywords"]: update})
    };

    return (
        <OverviewContext.Provider value={{
            context,
            setContext,
            addScheduleKeyword,
            editScheduleKeyword,
            deleteScheduleKeyword
        }}>
            {children}
        </OverviewContext.Provider>
    );
};

OverviewContextProvider.propTypes = {
    children: PropTypes.node,
};
