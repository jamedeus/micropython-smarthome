import React, { useState, createContext } from 'react';
import PropTypes from 'prop-types';
import { parse_dom_context } from 'util/django_util';


export const OverviewContext = createContext();

export const OverviewContextProvider = ({ children }) => {
    // Load context set by django template
    const [context, setContext] = useState(() => {
        return {
            not_uploaded: parse_dom_context("not_uploaded"),
            uploaded: parse_dom_context("uploaded"),
            client_ip: parse_dom_context("client_ip")
        };
    });

    const addNewNode = (friendly_name, filename, ip) => {
        let update = [ ...context.uploaded ];
        update.push({friendly_name: friendly_name, filename: filename, ip: ip});
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

    // Delete a config that has not been uploaded yet
    const deleteNewConfig = (filename) => {
        let update = [ ...context.not_uploaded ];
        update = update.filter(config => config.filename !== filename);
        setContext({ ...context, ["not_uploaded"]: update });
    };

    // Adds new config to uploaded, removes from not_uploaded
    const handleNewConfigUpload = (friendly_name, filename, ip) => {
        let uploaded = [ ...context.uploaded ];
        uploaded.push({friendly_name: friendly_name, filename: filename, ip: ip});
        let not_uploaded = [ ...context.not_uploaded ];
        not_uploaded = not_uploaded.filter(config => config.filename !== filename);
        setContext({
            ...context,
            ["uploaded"]: uploaded,
            ["not_uploaded"]: not_uploaded
        });
    };

    return (
        <OverviewContext.Provider value={{
            context,
            setContext,
            addNewNode,
            deleteExistingNode,
            changeExistingNodeIp,
            deleteNewConfig,
            handleNewConfigUpload
        }}>
            {children}
        </OverviewContext.Provider>
    );
};

OverviewContextProvider.propTypes = {
    children: PropTypes.node,
};
