import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import { sleep } from 'util/helper_functions';
import { formatIp, ipRegex } from 'util/validation';
import { send_post_request } from 'util/django_util';
import { ErrorModalContext } from 'modals/ErrorModal';

export const ChangeIpModalContext = createContext();

export const ChangeIpModalContextProvider = ({ children }) => {
    const [changeIpModalContent, setChangeIpModalContent] = useState({
        visible: false,
        stage: 'prompt',
        ipAddress: '',
        buttonDisabled: true
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

    async function changeIP() {
        // Start animation
        setChangeIpModalContent({ ...changeIpModalContent, ["stage"]: "loading" });

        // Send API call, wait for backend to download config file from target node
        const body = {
            'new_ip': changeIpModalContent.ipAddress ,
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
                ["body"]: changeIpModalContent.ipAddress
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
    }

    // Takes current value of IP field, enables upload button
    // if passes regex, otherwise disables upload button
    const isIpValid = (ip) => {
        if (ipRegex.test(ip)) {
            setChangeIpModalContent({ ...changeIpModalContent,
                ["buttonDisabled"]: false,
                ["ipAddress"]: ip
            });
        } else {
            setChangeIpModalContent({ ...changeIpModalContent,
                ["buttonDisabled"]: true,
                ["ipAddress"]: ip
            });
        }
    };

    // Handler for IP address field, formats IP as user types
    const setIp = (value) => {
        // Format value entered by user
        const newIP = formatIp(changeIpModalContent.ipAddress, value);
        // Enable upload button if IP is valid, set IP either way
        isIpValid(newIP);
    };

    return (
        <Modal show={changeIpModalContent.visible} onHide={handleClose} centered>
            <Modal.Header className="justify-content-between pb-0">
                <button type="button" className="btn-close" style={{visibility: "hidden"}}></button>
                <h5 className="modal-title">Change IP</h5>
                <button type="button" className="btn-close" onClick={() => handleClose()}></button>
            </Modal.Header>

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
                                        value={changeIpModalContent.ipAddress}
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
                    disabled={changeIpModalContent.buttonDisabled}
                    onClick={changeIP}
                >
                    Change
                </Button>
            </Modal.Footer>
        </Modal>
    );
};
