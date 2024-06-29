import React, { useState } from 'react';
import Dropdown from 'react-bootstrap/Dropdown';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import { send_post_request } from 'util/django_util';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';


export const WifiModal = () => {
    // Create state object to control visibility
    const [ show, setShow ] = useState(false);

    // Create state objects for ssid and password
    const [ ssid, setSsid ] = useState("");
    const [ password, setPassword ] = useState("");

    // Create state object for submit button enable state
    const [ submitDisabled, setSubmitDisabled ] = useState(true);

    // Submit handler, post credentials to backend and close modal
    const setWifiCredentials = () => {
        send_post_request(
            "set_default_credentials",
            {"ssid": ssid, "password": password}
        );
        setShow(false);
    };

    const updateSsid = (newSsid) => {
        setSsid(newSsid);
        if (newSsid !== "" && password !== "") {
            setSubmitDisabled(false);
        } else {
            setSubmitDisabled(true);
        }
    };

    const updatePassword = (newPassword) => {
        setPassword(newPassword);
        if (newPassword !== "" && ssid !== "") {
            setSubmitDisabled(false);
        } else {
            setSubmitDisabled(true);
        }
    };

    // Submit if enter key pressed in either field (ignore if either field empty)
    const handleEnterKey = (e) => {
        if (e.key === "Enter" && ssid !== "" && password !== "") {
            setWifiCredentials();
        }
    };

    return (
        <>
            <Dropdown.Item onClick={() => setShow(true)}>
                Set WIFI credentials
            </Dropdown.Item>

            <Modal show={show} onHide={() => setShow(false)} centered>
                <HeaderWithCloseButton
                    title="Set Default Wifi"
                    onClose={() => setShow(false)}
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
                        onChange={(e) => updateSsid(e.target.value)}
                        onKeyDown={handleEnterKey}
                    />

                    <Form.Label><b>Password:</b></Form.Label>
                    <Form.Control
                        type="password"
                        value={password}
                        onChange={(e) => updatePassword(e.target.value)}
                        onKeyDown={handleEnterKey}
                    />
                </Modal.Body>
                <Modal.Footer className="mx-auto pt-0">
                    <Button
                        variant="secondary"
                        onClick={() => setShow(false)}
                    >
                        Cancel
                    </Button>
                    <Button
                        variant="success"
                        onClick={setWifiCredentials}
                        disabled={submitDisabled}
                    >
                        OK
                    </Button>
                </Modal.Footer>
            </Modal>
        </>
    );
};
