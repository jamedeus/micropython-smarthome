import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import { HeaderStaticBackdrop } from 'modals/HeaderComponents';
import { LoadingSpinner } from 'util/animations';

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
    };

    return (
        <ErrorModalContext.Provider value={{
            errorModalContent,
            setErrorModalContent,
            handleClose
        }}>
            {children}
        </ErrorModalContext.Provider>
    );
};

ErrorModalContextProvider.propTypes = {
    children: PropTypes.node,
};

export const ErrorModal = () => {
    // Get state object that determines modal contents
    const { errorModalContent, handleClose } = useContext(ErrorModalContext);

    const Contents = () => {
        switch (errorModalContent.error) {
            case "failed":
                return <div className="text-center">{errorModalContent.body}</div>;
            case "unreachable":
                return (
                    <>
                        <p className="text-center">
                            Unable to connect to {errorModalContent.body}<br/>
                            Possible causes:
                        </p>
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
            case "confirm_delete":
                return <p>This cannot be undone - are you sure?</p>;
            case "failed_upload_all":
                return (
                    <ul>
                        {Object.keys(errorModalContent.body).map(node =>
                            <li key={node}>{node}: {errorModalContent.body[node]}</li>
                        )}
                    </ul>
                );
            case "connection_error":
                return (
                    <>
                        <p className="text-center pt-0">
                            Attempting to reestablish connection...
                        </p>
                        <LoadingSpinner size="medium" />
                    </>
                );
            default:
                return <p>{errorModalContent.body}</p>;
        }
    };

    const Footer = () => {
        switch (errorModalContent.error) {
            case "duplicate":
                return (
                    <>
                        <Button
                            variant="secondary"
                            className="m-1"
                            onClick={handleClose}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="danger"
                            className="m-1"
                            onClick={errorModalContent.handleConfirm}
                        >
                            Overwrite
                        </Button>
                    </>
                );
            case "unsaved_changes":
                return (
                    <>
                        <Button
                            variant="danger"
                            className="m-1"
                            onClick={errorModalContent.handleConfirm}
                        >
                            Go Back
                        </Button>
                        <Button
                            variant="secondary"
                            className="m-1"
                            onClick={handleClose}
                        >
                            Keep Editing
                        </Button>
                    </>
                );
            case "confirm_delete":
                return (
                    <>
                        <Button
                            variant="secondary"
                            className="m-1"
                            onClick={handleClose}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="danger"
                            className="m-1"
                            onClick={errorModalContent.handleConfirm}
                        >
                            Delete
                        </Button>
                    </>
                );
            case "connection_error":
                return (
                    <Button
                        variant="success"
                        className="m-1"
                        onClick={errorModalContent.handleConfirm}
                    >
                        Back to Overview
                    </Button>
                );
            default:
                return (
                    <Button
                        variant="success"
                        className="m-1"
                        onClick={handleClose}
                    >
                        OK
                    </Button>
                );
        }
    };

    return (
        <Modal
            show={errorModalContent.visible}
            onHide={handleClose}
            backdrop="static"
            keyboard={false}
            centered
        >
            <HeaderStaticBackdrop title={errorModalContent.title} />

            <Modal.Body className="d-flex flex-column text-center mx-auto">
                <Contents />
            </Modal.Body>
            <Modal.Footer className="mx-auto">
                <Footer />
            </Modal.Footer>
        </Modal>
    );
};
