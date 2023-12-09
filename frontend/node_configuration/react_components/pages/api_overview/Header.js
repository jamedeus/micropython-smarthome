import React from 'react';
import Dropdown from 'react-bootstrap/Dropdown';


const Header = () => {
    const rebootAll = () => {
        fetch("/reboot_all");
    };

    const resetAll = () => {
        fetch("/reset_all");
    };

    return (
        <div className="d-flex justify-content-between">
            <button type="button" className="btn my-auto" id="back_button" style={{visibility: "hidden"}}><i className="bi-list"></i></button>
            <h1 className="my-3">Api Overview</h1>
            <Dropdown align="end" className="my-auto">
                <Dropdown.Toggle variant="light" id="settings-button">
                    <i className="bi-list"></i>
                </Dropdown.Toggle>
                <Dropdown.Menu>
                    <Dropdown.Item onClick={rebootAll}>Reboot all</Dropdown.Item>
                    <Dropdown.Item onClick={resetAll}>Reset all rules</Dropdown.Item>
                </Dropdown.Menu>
            </Dropdown>
        </div>
    );
};


export default Header;
