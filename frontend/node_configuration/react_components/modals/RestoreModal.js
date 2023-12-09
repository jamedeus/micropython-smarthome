import React, { useContext, useState } from 'react';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import { sleep } from 'util/helper_functions';
import { formatIp, ipRegex } from 'util/validation';
import { send_post_request } from 'util/django_util';
import { ErrorModalContext } from 'modals/ErrorModal';
import { OverviewContext } from 'root/OverviewContext';
import { LoadingSpinner, CheckmarkAnimation } from 'util/animations';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';


export const RestoreModal = () => {
    // Get callback used to render new row after restoring node
    const { addNewNode } = useContext(OverviewContext);

    // Get callbacks for error modal
    const { errorModalContent, setErrorModalContent } = useContext(ErrorModalContext);

    // Create state object to control visibility
    const [ show, setShow ] = useState(false);

    // Create state object for stage (prompt, loading, complete)
    const [ stage, setStage ] = useState("prompt");

    // Create state object for IP field
    const [ ipAddress, setipAddress ] = useState("");

    // Create state object for submit button enable state
    const [ submitDisabled, setSubmitDisabled ] = useState(true);

    // Ensure stage is set to prompt when showing modal
    const showRestoreModal = () => {
        setStage("prompt");
        setShow(true);
    };

    async function restoreConfig() {
        // Start animation, disable submit button
        setStage("loading");
        setSubmitDisabled(true);

        // Send API call, wait for backend to download config file from target node
        const body = {'ip' : ipAddress };
        const response = await send_post_request("restore_config", body);

        // Restored successfully
        if (response.ok) {
            // Show success checkmark animation, wait for animation to complete
            setStage("complete");
            await sleep(1200);

            // Render new row, close modal
            const data = await response.json();
            addNewNode(data.friendly_name, data.ip);
            setShow(false);

        // Unreachable
        } else if (response.status == 404) {
            // Hide upload modal, show error modal with possible connection failure reasons
            setShow(false);
            setErrorModalContent({
                ...errorModalContent,
                ["visible"]: true,
                ["title"]: "Connection Error",
                ["error"]: "unreachable",
                ["body"]: ipAddress
            });

        // Duplicate
        } else if (response.status == 409) {
            // Hide upload modal, show error modal
            setShow(false);
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

        // Re-enable submit button
        setSubmitDisabled(false);
    }

    // Takes current value of IP field, enables upload button
    // if passes regex, otherwise disables upload button
    const isIpValid = (ip) => {
        if (ipRegex.test(ip)) {
            setSubmitDisabled(false);
            setipAddress(ip);
        } else {
            setSubmitDisabled(true);
            setipAddress(ip);
        }
    };

    // Handler for IP address field, formats IP as user types
    const setIp = (value) => {
        // Format value entered by user
        const newIP = formatIp(ipAddress, value);
        // Enable upload button if IP is valid, set IP either way
        isIpValid(newIP);
    };

    // Restore config if enter key pressed in field with valid IP
    const handleEnterKey = (e) => {
        if (e.key === "Enter" && !submitDisabled) {
            restoreConfig();
        }
    };

    return (
        <>
            <Dropdown.Item onClick={showRestoreModal}>Restore config</Dropdown.Item>

            <Modal show={show} onHide={() => setShow(false)} centered>
                <HeaderWithCloseButton title="Restore Config" onClose={() => setShow(false)} />

                <Modal.Body className="d-flex flex-column mx-auto text-center">
                    <p>This menu downloads config files from existing nodes and adds them to the database + frontend. This can be useful to rebuild the database if it is lost or corrupted.</p>
                    {(() => {
                        switch (stage) {
                            case "prompt":
                                return (
                                    <>
                                        <Form.Label><b>IP Address:</b></Form.Label>
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
                                return <CheckmarkAnimation size="large" />;
                        }
                    })()}
                </Modal.Body>
                <Modal.Footer className="mx-auto pt-0">
                    <Button variant="success" disabled={submitDisabled} onClick={restoreConfig} >
                        Restore
                    </Button>
                </Modal.Footer>
            </Modal>
        </>
    );
};
