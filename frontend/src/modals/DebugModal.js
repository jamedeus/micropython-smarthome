import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Modal from 'react-bootstrap/Modal';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';
import { ApiCardContext } from 'root/ApiCardContext';


export const DebugModalContext = createContext();

export const DebugModalContextProvider = ({ children }) => {
    const [debugModalContent, setDebugModalContent] = useState({
        visible: false,
        attributes: {}
    });

    // Get function to send API call to node
    const {send_command} = useContext(ApiCardContext);

    const handleClose = () => {
        setDebugModalContent({ ...debugModalContent, ["visible"]: false });
    };

    const getAttributes = async (id) => {
        // Get instance attributes from node
        const response = await send_command({'command': 'get_attributes', 'instance': id});
        const attributes = await response.json();
        return attributes;
    };

    const showDebugModal = async (id) => {
        const attributes = await getAttributes(id);
        setDebugModalContent({
            ...debugModalContent,
            ["visible"]: true,
            ["attributes"]: attributes
        });
    };

    return (
        <DebugModalContext.Provider value={{
            debugModalContent,
            setDebugModalContent,
            handleClose,
            showDebugModal
        }}>
            {children}
        </DebugModalContext.Provider>
    );
};

DebugModalContextProvider.propTypes = {
    children: PropTypes.node,
};


export const DebugModal = () => {
    // Get function used to make API call
    const {debugModalContent, handleClose} = useContext(DebugModalContext);

    return (
        <Modal show={debugModalContent.visible} onHide={handleClose} centered>
            <HeaderWithCloseButton title="Debug" onClose={handleClose} />

            <Modal.Body className="d-flex flex-column mx-auto text-center">
                <pre className='d-inline-block text-start section p-3' id="debug-json">
                    {JSON.stringify(debugModalContent.attributes, null, 4)}
                </pre>
            </Modal.Body>
        </Modal>
    );
};
