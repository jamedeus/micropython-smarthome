import React, { useState } from 'react';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import { send_post_request } from 'util/django_util';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';

export let showWifiModal;

const WifiModal = () => {
    // Create state object to control visibility
    const [ visible, setVisible ] = useState(false);

    // Create state objects for ssid and password
    const [ ssid, setSsid ] = useState("");
    const [ password, setPassword ] = useState("");

    showWifiModal = () => {
        setVisible(true);
    };

    // Submit handler, post credentials to backend and close modal
    const setWifiCredentials = () => {
        send_post_request(
            "set_default_credentials",
            {"ssid": ssid, "password": password}
        );
        setVisible(false);
    };

    // Submit if enter key pressed in either field (ignore if either field empty)
    const handleEnterKey = (e) => {
        if (e.key === "Enter" && ssid && password) {
            setWifiCredentials();
        }
    };

    return (
        <Modal show={visible} onHide={() => setVisible(false)} centered>
            <HeaderWithCloseButton
                title="Set Default Wifi"
                onClose={() => setVisible(false)}
            />

            <Modal.Body className="d-flex flex-column mx-auto">
                <p className="text-center">
                    These credentials will be pre-filled every time a new config is created
                </p>

                <Form.Label><b>Network:</b></Form.Label>
                <Form.Control
                    type="text"
                    className="mb-2"
                    value={ssid}
                    onChange={(e) => setSsid(e.target.value)}
                    onKeyDown={handleEnterKey}
                />

                <Form.Label><b>Password:</b></Form.Label>
                <Form.Control
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onKeyDown={handleEnterKey}
                />
            </Modal.Body>
            <Modal.Footer className="mx-auto pt-0">
                <Button
                    variant="secondary"
                    onClick={() => setVisible(false)}
                >
                    Cancel
                </Button>
                <Button
                    variant="success"
                    onClick={setWifiCredentials}
                    disabled={!(ssid && password)}
                >
                    OK
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default WifiModal;
