import React, { useState, createContext } from 'react';
import PropTypes from 'prop-types';
import { parse_dom_context } from 'util/django_util';


export const OverviewContext = createContext();

export const OverviewContextProvider = ({ children }) => {
    // Load context set by django template
    const [context, setContext] = useState(() => {
        return {
            not_uploaded: parse_dom_context("not_uploaded"),
            uploaded: parse_dom_context("uploaded")
        };
    });

    // Adds node to ExistingNodesTable (only used by RestoreModal)
    const addNewNode = (friendly_name, filename, ip) => {
        setContext({ ...context, uploaded: [
            ...context.uploaded,
            {friendly_name: friendly_name, filename: filename, ip: ip}
        ]});
    };

    // Deletes node from ExistingNodesTable
    const deleteExistingNode = (friendly_name) => {
        setContext({ ...context, uploaded: context.uploaded.filter(
            node => node.friendly_name !== friendly_name
        )});
    };

    // Changes IP of node on ExistingNodesTable
    const changeExistingNodeIp = (friendly_name, newIp) => {
        setContext({ ...context, uploaded: context.uploaded.map(node =>
            node.friendly_name === friendly_name ? { ...node, ip: newIp} : node
        )});
    };

    // Delete config from NewConfigTable
    const deleteNewConfig = (filename) => {
        setContext({ ...context, not_uploaded: context.not_uploaded.filter(
            config => config.filename !== filename
        )});
    };

    // Adds new node to ExistingNodesTable, removes config from NewConfigTable
    const handleNewConfigUpload = (friendly_name, filename, ip) => {
        const uploaded = [
            ...context.uploaded,
            {friendly_name: friendly_name, filename: filename, ip: ip}
        ];
        const not_uploaded = context.not_uploaded.filter(
            config => config.filename !== filename
        );
        setContext({ ...context,
            uploaded: uploaded,
            not_uploaded: not_uploaded
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
