import React, { useContext, useState } from 'react';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import { sleep } from 'util/helper_functions';
import { formatIp, ipRegex } from 'util/validation';
import { send_post_request } from 'util/django_util';
import { showErrorModal } from 'modals/ErrorModal';
import { OverviewContext } from 'root/OverviewContext';
import { LoadingSpinner, CheckmarkAnimation } from 'util/animations';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';

export let showRestoreModal;

export const RestoreModal = () => {
    // Get callback used to render new row after restoring node
    const { addNewNode } = useContext(OverviewContext);

    // Create states for visibility, stage (prompt, loading, complete), input
    const [ visible, setVisible ] = useState(false);
    const [ stage, setStage ] = useState("prompt");
    const [ ipAddress, setipAddress ] = useState("");

    // Ensure stage is set to prompt when showing modal
    showRestoreModal = () => {
        setStage("prompt");
        setVisible(true);
    };

    const restoreConfig = async () => {
        // Start animation (disables submit button)
        setStage("loading");

        // Send API call, wait for backend to download config file from target node
        const body = {'ip' : ipAddress };
        const response = await send_post_request("/restore_config", body);

        // Restored successfully
        if (response.ok) {
            // Show success checkmark animation, wait for animation to complete
            setStage("complete");
            await sleep(1200);

            // Render new row, close modal
            const data = await response.json();
            addNewNode(data.friendly_name, data.filename, data.ip);
            setVisible(false);

        // Unreachable
        } else if (response.status == 404) {
            // Hide upload modal, show error modal with possible connection failure reasons
            setVisible(false);
            showErrorModal({
                title: "Connection Error",
                error: "unreachable",
                body: ipAddress
            });

        // Duplicate
        } else if (response.status == 409) {
            // Hide upload modal, show error modal
            setVisible(false);
            showErrorModal({
                title: "Duplicate",
                error: "",
                body: "A node with the same name or filename already exists"
            });

        // Other error, show in alert
        } else {
            const error = await response.json();
            alert(JSON.stringify(error));
        }
    };

    // Handler for IP address field, formats IP as user types
    const setIp = (value) => {
        setipAddress(formatIp(ipAddress, value));
    };

    // Restore config if enter key pressed in field with valid IP
    const handleEnterKey = (e) => {
        if (e.key === "Enter" && ipRegex.test(ipAddress)) {
            restoreConfig();
        }
    };

    return (
        <Modal show={visible} onHide={() => setVisible(false)} centered>
            <HeaderWithCloseButton
                title="Restore Config"
                onClose={() => setVisible(false)}
            />

            <Modal.Body className="d-flex flex-column mx-auto text-center">
                <p>This menu downloads config files from existing nodes and adds them to the database + frontend. This can be useful to rebuild the database if it is lost or corrupted.</p>
                {(() => {
                    switch (stage) {
                        case "prompt":
                            return (
                                <>
                                    <Form.Label className="fw-bold">
                                        IP Address:
                                    </Form.Label>
                                    <Form.Control
                                        type="text"
                                        value={ipAddress}
                                        onChange={(e) => setIp(e.target.value)}
                                        onKeyDown={handleEnterKey}
                                    />
                                </>
                            );
                        case "loading":
                            return <LoadingSpinner size="medium" />;
                        case "complete":
                            return <CheckmarkAnimation size="large" color="green" />;
                    }
                })()}
            </Modal.Body>
            <Modal.Footer className="mx-auto pt-0">
                <Button
                    variant="success"
                    disabled={!ipRegex.test(ipAddress)}
                    onClick={restoreConfig}
                >
                    Restore
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default RestoreModal;
