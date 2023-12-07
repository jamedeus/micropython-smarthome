import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import { sleep } from 'util/helper_functions';
import { formatIp, ipRegex } from 'util/validation';
import { send_post_request } from 'util/django_util';
import { ErrorModalContext } from 'modals/ErrorModal';
import { LoadingSpinner, CheckmarkAnimation } from 'modals/animations';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';

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

    // Restore config if enter key pressed in field with valid IP
    const handleEnterKey = (e) => {
        if (e.key === "Enter" && !restoreModalContent.buttonDisabled) {
            restoreConfig();
        }
    };

    return (
        <Modal show={restoreModalContent.visible} onHide={handleClose} centered>
            <HeaderWithCloseButton title="Restore Config" onClose={handleClose} />

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
                                        onKeyDown={handleEnterKey}
                                    />
                                </>
                            );
                        case "loading":
                            return <LoadingSpinner />;
                        case "complete":
                            return <CheckmarkAnimation />;
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
