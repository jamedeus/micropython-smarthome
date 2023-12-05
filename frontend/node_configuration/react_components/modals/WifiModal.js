import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import { send_post_request } from 'util/django_util';

export const WifiModalContext = createContext();

export const WifiModalContextProvider = ({ children }) => {
    // Create state object to control visibility
    const [ show, setShow ] = useState(false);

    const handleClose = () => {
        setShow(false);
    };

    const showWifiModal = () => {
        setShow(true);
    };

    return (
        <WifiModalContext.Provider value={{ show, handleClose, showWifiModal }}>
            {children}
        </WifiModalContext.Provider>
    );
};

WifiModalContextProvider.propTypes = {
    children: PropTypes.node,
};

export const WifiModal = () => {
    // Get state object that controls visibility
    const { show, handleClose } = useContext(WifiModalContext);

    // Create state objects for ssid and password
    const [ ssid, setSsid ] = useState("");
    const [ password, setPassword ] = useState("");

    // Submit handler, post credentials to backend and close modal
    const setWifiCredentials = () => {
        send_post_request("set_default_credentials", {"ssid": ssid, "password": password});
        handleClose()
    };

    return (
        <Modal show={show} onHide={handleClose} centered>
            <Modal.Header className="justify-content-between pb-0">
                <button type="button" className="btn-close" style={{visibility: "hidden"}}></button>
                <h5 className="modal-title">Default Wifi</h5>
                <button type="button" className="btn-close" onClick={() => handleClose()}></button>
            </Modal.Header>

            <Modal.Body className="d-flex flex-column mx-auto">
                <p className="text-center">These credentials will be pre-filled every time a new config is created</p>

                <Form.Label><b>Network:</b></Form.Label>
                <Form.Control type="text" value={ssid} onChange={(e) => setSsid(e.target.value)} className="mb-2"/>

                <Form.Label><b>Password:</b></Form.Label>
                <Form.Control type="password" value={password} onChange={(e) => setPassword(e.target.value)}/>
            </Modal.Body>
            <Modal.Footer className="mx-auto pt-0">
                <Button variant="secondary" onClick={handleClose}>Cancel</Button>
                <Button variant="success" onClick={setWifiCredentials}>OK</Button>
            </Modal.Footer>
        </Modal>
    );
};
