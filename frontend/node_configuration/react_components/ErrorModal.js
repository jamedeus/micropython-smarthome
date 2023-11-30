import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';

export const ErrorModalContext = createContext();

export const ErrorModalContextProvider = ({ children }) => {
    const [errorModalContent, setErrorModalContent] = useState({
        visible: false,
        title: '',
        error: false,
        body: ''
    });

    const handleClose = () => {
        setErrorModalContent({ ...errorModalContent, ["visible"]: false });
    }

    return (
        <ErrorModalContext.Provider value={{ errorModalContent, setErrorModalContent, handleClose }}>
            {children}
        </ErrorModalContext.Provider>
    );
};

export const ErrorModal = () => {
    // Get state object that determines modal contents
    const { errorModalContent, handleClose } = useContext(ErrorModalContext);

    return (
        <Modal show={errorModalContent.visible} onHide={handleClose} centered>
            <Modal.Header className="justify-content-between">
                <h3 className="modal-title mx-auto">{errorModalContent.title}</h3>
            </Modal.Header>

            <Modal.Body className="d-flex flex-column mx-auto">
                {(() => {
                    switch (errorModalContent.error) {
                        case "unreachable":
                            return (
                                <>
                                    <p className="text-center">Unable to connect to {errorModalContent.body}<br/>Possible causes:</p>
                                    <ul>
                                        <li>Node is not connected to wifi</li>
                                        <li>Node IP has changed</li>
                                        <li>Node has not run webrepl_setup</li>
                                    </ul>
                                </>
                            );
                        case "failed":
                            return <div className="text-center">{errorModalContent.body}</div>;
                    }
                })()}
            </Modal.Body>
            <Modal.Footer className="mx-auto">
                <Button variant="success" className="m-1" onClick={handleClose}>OK</Button>
            </Modal.Footer>
        </Modal>
    );
};
