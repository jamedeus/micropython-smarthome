import React, { useState } from 'react';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import { HeaderStaticBackdrop } from 'modals/HeaderComponents';
import { LoadingSpinner } from 'util/animations';

export let showErrorModal;

export let hideErrorModal;

const ErrorModal = () => {
    const [errorModalContent, setErrorModalContent] = useState({
        visible: false,
        title: '',
        error: false,
        body: '',
        handleConfirm: ''
    });

    hideErrorModal = () => {
        setErrorModalContent({ ...errorModalContent, visible: false });
    };

    // Takes partial or full list or params, concatenates with existing state
    showErrorModal = (errorModalParams) => {
        setErrorModalContent({ ...errorModalContent,
            visible: true,
            ...errorModalParams
        });
    };

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
                            <li className="text-start">
                                Node is not connected to wifi
                            </li>
                            <li className="text-start">
                                Node IP has changed
                            </li>
                            <li className="text-start">
                                Node has not run webrepl_setup
                            </li>
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
                            onClick={hideErrorModal}
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
                            onClick={hideErrorModal}
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
                            onClick={hideErrorModal}
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
                        onClick={hideErrorModal}
                    >
                        OK
                    </Button>
                );
        }
    };

    return (
        <Modal
            show={errorModalContent.visible}
            onHide={hideErrorModal}
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

export default ErrorModal;
