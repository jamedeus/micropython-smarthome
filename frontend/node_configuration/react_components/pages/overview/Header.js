import React from 'react';
import Dropdown from 'react-bootstrap/Dropdown';


const Header = () => {
    // Render full layout with metadata, wifi, IR Blaster, and instance cards
    return (
        <div className="d-flex justify-content-between">
            <button type="button" className="btn my-auto" id="back_button" style={{visibility: "hidden"}}><i className="bi-chevron-left"></i></button>
            <h1 className="my-3">Configure Nodes</h1>
            <Dropdown className="my-auto">
                <Dropdown.Toggle variant="dark" id="settings-button">
                    <i className="bi-gear-fill"></i>
                </Dropdown.Toggle>
                <Dropdown.Menu>
                    <Dropdown.Item>Set WIFI credentials</Dropdown.Item>
                    <Dropdown.Item>Set GPS coordinates</Dropdown.Item>
                    <Dropdown.Item>Re-upload all</Dropdown.Item>
                    <Dropdown.Item>Restore config</Dropdown.Item>
                    <Dropdown.Item>Desktop integration</Dropdown.Item>
                </Dropdown.Menu>
            </Dropdown>
        </div>
    );
};


export default Header;
