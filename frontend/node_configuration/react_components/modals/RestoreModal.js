import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import { sleep } from 'util/helper_functions';
import { formatIp, ipRegex } from 'util/validation';
import { send_post_request } from 'util/django_util';
import { ErrorModalContext } from 'modals/ErrorModal';

export const RestoreModalContext = createContext();

export const RestoreModalContextProvider = ({ children }) => {
    const [restoreModalContent, setRestoreModalContent] = useState({
        visible: false,
        stage: 'prompt',
        ipAddress: '',
        buttonDisabled: true
    });

    const handleClose = () => {
        setRestoreModalContent({ ...restoreModalContent, ["visible"]: false });
    };

    const showRestoreModal = () => {
        setRestoreModalContent({
            ...restoreModalContent,
            ["visible"]: true,
            ["stage"]: "prompt"
        });
    };

    return (
        <RestoreModalContext.Provider value={{
            restoreModalContent,
            setRestoreModalContent,
            handleClose,
            showRestoreModal
        }}>
            {children}
        </RestoreModalContext.Provider>
    );
};

RestoreModalContextProvider.propTypes = {
    children: PropTypes.node,
};

export const RestoreModal = () => {
    // Get state object that determines modal contents
    const { restoreModalContent, setRestoreModalContent, handleClose } = useContext(RestoreModalContext);

    // Get callbacks for error modal
    const { errorModalContent, setErrorModalContent } = useContext(ErrorModalContext);

    async function restoreConfig() {
        // Start animation
        setRestoreModalContent({ ...restoreModalContent, ["stage"]: "loading" });

        // Send API call, wait for backend to download config file from target node
        const body = {'ip' : restoreModalContent.ipAddress };
        const response = await send_post_request("restore_config", body);

        // Restored successfully
        if (response.ok) {
            // Show success checkmark animation
            setRestoreModalContent({ ...restoreModalContent, ["stage"]: "complete" });

            // Wait for animation to complete before reloading
            await sleep(1200);
            location.reload();

        // Unreachable
        } else if (response.status == 404) {
            // Hide upload modal (set same stage to prevent visual flash)
            setRestoreModalContent({
                ...restoreModalContent,
                ["visible"]: false,
                ["stage"]: "loading"
            });
            // Show error modal with possible connection failure reasons
            setErrorModalContent({
                ...errorModalContent,
                ["visible"]: true,
                ["title"]: "Connection Error",
                ["error"]: "unreachable",
                ["body"]: restoreModalContent.ipAddress
            });

        // Duplicate
        } else if (response.status == 409) {
            // Hide upload modal (set same stage to prevent visual flash)
            setRestoreModalContent({
                ...restoreModalContent,
                ["visible"]: false,
                ["stage"]: "loading"
            });
            // Show error modal
            setErrorModalContent({
                ...errorModalContent,
                ["visible"]: true,
                ["title"]: "Duplicate",
                ["error"]: "",
                ["body"]: "A node with the same name or filename already exists"
            });

        // Other error, show in alert
        } else {
            alert(await response.text());
        }
    }

    // Takes current value of IP field, enables upload button
    // if passes regex, otherwise disables upload button
    const isIpValid = (ip) => {
        if (ipRegex.test(ip)) {
            setRestoreModalContent({ ...restoreModalContent,
                ["buttonDisabled"]: false,
                ["ipAddress"]: ip
            });
        } else {
            setRestoreModalContent({ ...restoreModalContent,
                ["buttonDisabled"]: true,
                ["ipAddress"]: ip
            });
        }
    };

    // Handler for IP address field, formats IP as user types
    const setIp = (value) => {
        // Format value entered by user
        const newIP = formatIp(restoreModalContent.ipAddress, value);
        // Enable upload button if IP is valid, set IP either way
        isIpValid(newIP);
    };

    return (
        <Modal show={restoreModalContent.visible} onHide={handleClose} centered>
            <Modal.Header className="justify-content-between pb-0">
                <button type="button" className="btn-close" style={{visibility: "hidden"}}></button>
                <h5 className="modal-title">Restore Config</h5>;
                <button type="button" className="btn-close" onClick={() => handleClose()}></button>
            </Modal.Header>

            <Modal.Body className="d-flex flex-column mx-auto text-center">
                <p>This menu downloads config files from existing nodes and adds them to the database + frontend. This can be useful to rebuild the database if it is lost or corrupted.</p>
                {(() => {
                    switch (restoreModalContent.stage) {
                        case "prompt":
                            return (
                                <>
                                    <Form.Label><b>IP Address:</b></Form.Label>
                                    <Form.Control
                                        type="text"
                                        value={restoreModalContent.ipAddress}
                                        onChange={(e) => setIp(e.target.value)}
                                    />
                                </>
                            );
                        case "loading":
                            return (
                                <div className="spinner-border mx-auto" style={{width: "3rem", height: "3rem"}} role="status">
                                    <span className="visually-hidden">Loading...</span>
                                </div>
                            );
                        case "complete":
                            return (
                                <svg className="checkmark mx-auto" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                                    <circle className="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
                                    <path className="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                                </svg>
                            );
                    }
                })()}
            </Modal.Body>
            <Modal.Footer className="mx-auto pt-0">
                <Button
                    variant="success"
                    disabled={restoreModalContent.buttonDisabled}
                    onClick={restoreConfig}
                >
                    Restore
                </Button>
            </Modal.Footer>
        </Modal>
    );
};
