import React, { useState } from 'react';
import Dropdown from 'react-bootstrap/Dropdown';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import { client_ip, desktop_integration_link } from 'util/django_util';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';


export const DesktopModal = () => {
    // Create state object to set visiblity
    const [visible, setVisible] = useState(false);

    return (
        <>
            <Dropdown.Item onClick={() => setVisible(true)}>
                Desktop integration
            </Dropdown.Item>

            <Modal show={visible} onHide={() => setVisible(false)} centered>
                <HeaderWithCloseButton
                    title="Install Desktop Integration"
                    onClose={() => setVisible(false)}
                />

                <Modal.Body>
                    <p className="text-center mt-3">
                        This software integrates your computer into your smarthome:
                    </p>
                    <ul>
                        <li>Allow sensors to turn your computer screen on and off</li>
                        <li>Turn other devices on when your screen is on</li>
                        <li>Turn other devices off when your screen goes to sleep</li>
                    </ul>
                    <p className="text-center">
                        You can enable any or all of these functions by adding <b>desktop</b> type devices and/or sensors on any node.
                    </p>
                    <p className="text-center">
                        Your IP address is:
                    </p>
                    <h4 className="text-center">
                        <b>{client_ip}</b>
                    </h4>
                    <p className="text-center mt-4">
                        To install, click the download button, unzip the file, and run <b>setup.sh</b>
                    </p>
                </Modal.Body>
                <Modal.Footer className="mx-auto">
                    <Button variant="success" href={desktop_integration_link}>
                        Download
                    </Button>
                </Modal.Footer>
            </Modal>
        </>
    );
};
