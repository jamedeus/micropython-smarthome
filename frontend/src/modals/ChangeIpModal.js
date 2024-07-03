import React, { useContext, useState } from 'react';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import { sleep } from 'util/helper_functions';
import { formatIp, ipRegex } from 'util/validation';
import { send_post_request } from 'util/django_util';
import { ErrorModalContext } from 'modals/ErrorModal';
import { OverviewContext } from 'root/OverviewContext';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';
import { LoadingSpinner, CheckmarkAnimation } from 'util/animations';

export let showChangeIpModal;

const ChangeIpModal = () => {
    // Get context hook used to re-render with new IP
    const { changeExistingNodeIp } = useContext(OverviewContext);

    // Get callbacks for error modal
    const { errorModalContent, setErrorModalContent } = useContext(ErrorModalContext);

    // Create states for visibility, animation, input
    const [visible, setVisible] = useState(false);
    const [stage, setStage] = useState('prompt');
    const [target, setTarget] = useState('');
    const [ipAddress, setIpAddress] = useState("");

    showChangeIpModal = (friendly_name, ip) => {
        setStage('prompt');
        setTarget(friendly_name);
        setIpAddress(ip);
        setVisible(true);
    };

    const changeIP = async () => {
        // Start animation (disables submit button)
        setStage("loading");

        // Send API call, wait for backend to download config file from target node
        const body = {
            'new_ip': ipAddress,
            'friendly_name': target
        };
        const response = await send_post_request("change_node_ip", body);

        // Restored successfully
        if (response.ok) {
            // Show success checkmark animation, update IP in context state
            setStage("complete");
            changeExistingNodeIp(target, ipAddress);

            // Wait for animation to complete before hiding modal
            await sleep(1200);
            setVisible(false);

        // Unreachable
        } else if (response.status == 404) {
            // Hide modal, show error modal with possible connection failure reasons
            setVisible(false);
            setErrorModalContent({
                ...errorModalContent,
                ["visible"]: true,
                ["title"]: "Connection Error",
                ["error"]: "unreachable",
                ["body"]: ipAddress
            });

        // Other error, show in modal
        } else {
            // Hide modal, show error modal with response from backend
            setVisible(false);
            setErrorModalContent({
                ...errorModalContent,
                ["visible"]: true,
                ["title"]: "Error",
                ["error"]: "",
                ["body"]: await response.text()
            });
        }
    };

    // Handler for IP address field, formats IP as user types
    const setIp = (value) => {
        setIpAddress(formatIp(ipAddress, value));
    };

    // Change IP if enter key pressed in field with valid IP
    const handleEnterKey = (e) => {
        if (e.key === "Enter" && ipRegex.test(ipAddress)) {
            changeIP();
        }
    };

    return (
        <Modal show={visible} onHide={() => setVisible(false)} centered>
            <HeaderWithCloseButton
                title="Change IP"
                onClose={() => setVisible(false)}
            />

            <Modal.Body className="d-flex flex-column mx-auto text-center">
                <p>Upload an existing config file to a new IP</p>
                <p>This has no effect on the existing node, don&lsquo;t forget to upload another config or unplug it</p>
                {(() => {
                    switch (stage) {
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
                            return (
                                <LoadingSpinner
                                    size="medium"
                                    classes={["my-2"]}
                                />
                            );
                        case "complete":
                            return (
                                <CheckmarkAnimation
                                    size="large"
                                    color="green"
                                    classes={["my-2"]}
                                />
                            );
                    }
                })()}
            </Modal.Body>
            <Modal.Footer className="mx-auto pt-0">
                <Button
                    variant="success"
                    disabled={!ipRegex.test(ipAddress) && stage === 'prompt'}
                    onClick={changeIP}
                >
                    Change
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default ChangeIpModal;
