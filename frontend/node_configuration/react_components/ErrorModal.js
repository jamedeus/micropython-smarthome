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
        body: '',
        handleConfirm: ''
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

ErrorModalContextProvider.propTypes = {
    children: PropTypes.node,
}

export const ErrorModal = () => {
    // Get state object that determines modal contents
    const { errorModalContent, handleClose } = useContext(ErrorModalContext);

    return (
        <Modal show={errorModalContent.visible} onHide={handleClose} centered>
            <Modal.Header className="justify-content-between">
                <h3 className="modal-title mx-auto">{errorModalContent.title}</h3>
            </Modal.Header>

            <Modal.Body className="d-flex flex-column text-center mx-auto">
                {(() => {
                    switch (errorModalContent.error) {
                        case "failed":
                            return <div className="text-center">{errorModalContent.body}</div>;
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
                        case "duplicate":
                            return (
                                <>
                                    <p>You are about to overwrite <b>{errorModalContent.body}</b>, an existing config.</p>
                                    <p>This cannot be undone - are you sure?</p>
                                </>
                            );
                        case "unsaved_changes":
                            return <p>Your changes will be lost if you go back - are you sure?</p>;

                    }
                })()}
            </Modal.Body>
            <Modal.Footer className="mx-auto">
                {(() => {
                    switch (errorModalContent.error) {
                        case "duplicate":
                            return (
                                <>
                                    <Button variant="secondary" className="m-1" onClick={handleClose}>Cancel</Button>
                                    <Button variant="danger" className="m-1" onClick={errorModalContent.handleConfirm}>Overwrite</Button>
                                </>
                            );
                        case "unsaved_changes":
                            return (
                                <>
                                    <Button variant="danger" className="m-1" onClick={errorModalContent.handleConfirm}>Go Back</Button>
                                    <Button variant="secondary" className="m-1" onClick={handleClose}>Keep Editing</Button>
                                </>
                            );
                        default:
                            return <Button variant="success" className="m-1" onClick={handleClose}>OK</Button>;
                    }
                })()}
            </Modal.Footer>
        </Modal>
    );
};
