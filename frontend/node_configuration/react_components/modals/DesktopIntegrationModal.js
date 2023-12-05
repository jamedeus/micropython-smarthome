import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import { client_ip, desktop_integration_link } from 'util/django_util';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';

export const DesktopModalContext = createContext();

export const DesktopModalContextProvider = ({ children }) => {
    // Create state object to set visiblity
    const [visible, setVisible] = useState(false);

    const handleClose = () => {
        setVisible(false);
    };

    const showDesktopModal = () => {
        setVisible(true);
    };

    return (
        <DesktopModalContext.Provider value={{ visible, setVisible, showDesktopModal, handleClose }}>
            {children}
        </DesktopModalContext.Provider>
    );
};

DesktopModalContextProvider.propTypes = {
    children: PropTypes.node,
};

export const DesktopModal = () => {
    // Get state object that determines modal visibility
    const { visible, handleClose } = useContext(DesktopModalContext);

    return (
        <Modal show={visible} onHide={handleClose} centered>
            <HeaderWithCloseButton title="Install Desktop Integration" onClose={handleClose} />

            <Modal.Body>
                <p className="text-center mt-3">This software integrates your computer into your smarthome:</p>
                <ul>
                    <li>Allow sensors to turn your computer screen on and off</li>
                    <li>Turn other devices on when your screen is on</li>
                    <li>Turn other devices off when your screen goes to sleep</li>
                </ul>
                <p className="text-center">You can enable any or all of these functions by adding <b>desktop</b> type devices and/or sensors on any node.</p>
                <p className="text-center">Your IP address is:</p>
                <h4 className="text-center"><b>{client_ip}</b></h4>
                <p className="text-center mt-4">To install, click the download button, unzip the file, and run <b>setup.sh</b></p>
            </Modal.Body>
            <Modal.Footer className="mx-auto">
                <Button variant="success" href={desktop_integration_link}>
                    Download
                </Button>
            </Modal.Footer>
        </Modal>
    );
};
