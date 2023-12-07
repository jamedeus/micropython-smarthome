import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import { sleep } from 'util/helper_functions';
import { formatIp, ipRegex } from 'util/validation';
import { send_post_request } from 'util/django_util';
import { ErrorModalContext } from 'modals/ErrorModal';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';
import { LoadingSpinner, CheckmarkAnimation } from 'modals/animations';

export const ChangeIpModalContext = createContext();

export const ChangeIpModalContextProvider = ({ children }) => {
    const [changeIpModalContent, setChangeIpModalContent] = useState({
        visible: false,
        stage: 'prompt'
    });

    const handleClose = () => {
        setChangeIpModalContent({ ...changeIpModalContent, ["visible"]: false });
    };

    const showChangeIpModal = (friendly_name) => {
        setChangeIpModalContent({
            ...changeIpModalContent,
            ["visible"]: true,
            ["stage"]: "prompt",
            ["friendly_name"]: friendly_name
        });
    };

    return (
        <ChangeIpModalContext.Provider value={{
            changeIpModalContent,
            setChangeIpModalContent,
            handleClose,
            showChangeIpModal
        }}>
            {children}
        </ChangeIpModalContext.Provider>
    );
};

ChangeIpModalContextProvider.propTypes = {
    children: PropTypes.node,
};


export const ChangeIpModal = () => {
    // Get state object that determines modal contents
    const { changeIpModalContent, setChangeIpModalContent, handleClose } = useContext(ChangeIpModalContext);

    // Get callbacks for error modal
    const { errorModalContent, setErrorModalContent } = useContext(ErrorModalContext);

    // Create state object for IP field
    const [ ipAddress, setipAddress ] = useState("");

    // Create state object for submit button enable state
    const [ submitDisabled, setSubmitDisabled ] = useState(true);

    async function changeIP() {
        // Start animation, disable submit button
        setChangeIpModalContent({ ...changeIpModalContent, ["stage"]: "loading" });
        setSubmitDisabled(true);

        // Send API call, wait for backend to download config file from target node
        const body = {
            'new_ip': ipAddress,
            'friendly_name': changeIpModalContent.friendly_name
        };
        const response = await send_post_request("change_node_ip", body);

        // Restored successfully
        if (response.ok) {
            // Show success checkmark animation
            setChangeIpModalContent({ ...changeIpModalContent, ["stage"]: "complete" });

            // Wait for animation to complete before reloading
            await sleep(1200);
            location.reload();

        // Unreachable
        } else if (response.status == 404) {
            // Hide modal (set same stage to prevent visual flash)
            setChangeIpModalContent({
                ...changeIpModalContent,
                ["visible"]: false,
                ["stage"]: "loading"
            });
            // Show error modal with possible connection failure reasons
            setErrorModalContent({
                ...errorModalContent,
                ["visible"]: true,
                ["title"]: "Connection Error",
                ["error"]: "unreachable",
                ["body"]: ipAddress
            });

        // Other error, show in modal
        } else {
            // Hide modal (set same stage to prevent visual flash)
            setChangeIpModalContent({
                ...changeIpModalContent,
                ["visible"]: false,
                ["stage"]: "loading"
            });
            // Show error modal with response from backend
            setErrorModalContent({
                ...errorModalContent,
                ["visible"]: true,
                ["title"]: "Error",
                ["error"]: "",
                ["body"]: await response.text()
            });
        }

        // Re-enable submit button
        setSubmitDisabled(false);
    }

    // Takes current value of IP field, enables upload button
    // if passes regex, otherwise disables upload button
    const isIpValid = (ip) => {
        setipAddress(ip);
        if (ipRegex.test(ip)) {
            setSubmitDisabled(false);
        } else {
            setSubmitDisabled(true);
        }
    };

    // Handler for IP address field, formats IP as user types
    const setIp = (value) => {
        // Format value entered by user
        const newIP = formatIp(ipAddress, value);
        // Enable upload button if IP is valid, set IP either way
        isIpValid(newIP);
    };

    // Change IP if enter key pressed in field with valid IP
    const handleEnterKey = (e) => {
        if (e.key === "Enter" && !submitDisabled) {
            changeIP();
        }
    };

    return (
        <Modal show={changeIpModalContent.visible} onHide={handleClose} centered>
            <HeaderWithCloseButton title="Change IP" onClose={handleClose} />

            <Modal.Body className="d-flex flex-column mx-auto text-center">
                <p>Upload an existing config file to a new IP</p>
                <p>This has no effect on the existing node, don&lsquo;t forget to upload another config or unplug it</p>
                {(() => {
                    switch (changeIpModalContent.stage) {
                        case "prompt":
                            return (
                                <>
                                    <Form.Label><b>New IP:</b></Form.Label>
                                    <Form.Control
                                        type="text"
                                        value={ipAddress}
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
                <Button variant="success" disabled={submitDisabled} onClick={changeIP} >
                    Change
                </Button>
            </Modal.Footer>
        </Modal>
    );
};
