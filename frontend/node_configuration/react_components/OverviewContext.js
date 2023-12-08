import React, { useState, createContext } from 'react';
import PropTypes from 'prop-types';
import { v4 as uuid } from 'uuid';


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
        let update = [ ...context.schedule_keywords ];
        update.push({id: uuid(), keyword: keyword, timestamp: timestamp});
        setContext({ ...context, ["schedule_keywords"]: update});
    };

    const editScheduleKeyword = (keyword_old, keyword_new, timestamp_new) => {
        let update = [ ...context.schedule_keywords ];
        update = update.map(item =>
            item.keyword === keyword_old ? { ...item, keyword: keyword_new, timestamp: timestamp_new} : item
        );
        setContext({ ...context, ["schedule_keywords"]: update});
    };

    const deleteScheduleKeyword = (keyword) => {
        let update = [ ...context.schedule_keywords ];
        update = update.filter(item => item.keyword !== keyword);
        setContext({ ...context, ["schedule_keywords"]: update});
    };

    const addNewNode = (friendly_name, ip) => {
        let update = [ ...context.uploaded ];
        update.push({friendly_name: friendly_name, ip: ip})
        setContext({ ...context, ["uploaded"]: update});
    };

    const deleteExistingNode = (friendly_name) => {
        let update = [ ...context.uploaded ];
        update = update.filter(node => node.friendly_name !== friendly_name);
        setContext({ ...context, ["uploaded"]: update});
    };

    const changeExistingNodeIp = (friendly_name, newIp) => {
        let update = [ ...context.uploaded ];
        update = update.map(node => {
            if (node.friendly_name === friendly_name) {
                return { ...node, ip: newIp };
            }
            return node;
        });
        setContext({ ...context, ["uploaded"]: update});
    };

    return (
        <OverviewContext.Provider value={{
            context,
            setContext,
            addScheduleKeyword,
            editScheduleKeyword,
            deleteScheduleKeyword,
            addNewNode,
            deleteExistingNode,
            changeExistingNodeIp
        }}>
            {children}
        </OverviewContext.Provider>
    );
};

OverviewContextProvider.propTypes = {
    children: PropTypes.node,
};
