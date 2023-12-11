import React, { useContext } from 'react';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import { ApiCardContext } from 'root/ApiCardContext';


const Header = () => {
    // Get status object, function to make API calls
    const {status, send_command} = useContext(ApiCardContext);

    // Back button callback, redirect to overview
    const overview = () => {
        window.location.href = "/api";
    };

    // Dropdown menu callbacks, send API commands
    const reboot = () => {
        send_command({'command': 'reboot'});
    };

    const clearLog = () => {
        send_command({'command': 'clear_log'});
    };

    const resetAllRules = () => {
        send_command({'command': 'reset_all_rules'});
    };

    return (
        <div className="d-flex justify-content-between">
            <Button variant="dark" className="my-auto" onClick={overview}><i className="bi-chevron-left"></i></Button>
            <h1 className="my-3">{status.metadata.id}</h1>
            <Dropdown align="end" className="my-auto">
                <Dropdown.Toggle variant="light" id="settings-button">
                    <i className="bi-list"></i>
                </Dropdown.Toggle>
                <Dropdown.Menu>
                    <Dropdown.Item onClick={reboot}>Reboot</Dropdown.Item>
                    <Dropdown.Item onClick={clearLog}>Clear Log</Dropdown.Item>
                    <Dropdown.Item onClick={resetAllRules}>Reset all rules</Dropdown.Item>
                </Dropdown.Menu>
            </Dropdown>
        </div>
    );
};


export default Header;
