import React, { useState, useContext } from 'react';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import Collapse from 'react-bootstrap/Collapse';
import { ApiCardContext } from 'root/ApiCardContext';


const SensorCard = ({ id, params }) => {
    // Create state for trigger button
    const [triggered, setTriggered] = useState(false);

    // Create state for enable status
    const [enabled, setEnabled] = useState(params.enabled);

    return (
        <Card className="mb-4">
            <Card.Body className="d-flex flex-column">
                <div className="d-flex justify-content-between">
                    <Button
                        variant="outline-primary"
                        className="trigger-button my-auto me-auto"
                    >
                        <i className="bi-exclamation-lg"></i>
                    </Button>

                    <h4 className="card-title mx-auto my-auto">
                        {params.nickname}
                    </h4>

                    <Dropdown align="end" className="ms-auto my-auto">
                        <Dropdown.Toggle variant="outline-secondary" className="menu-button">
                            <i className="bi-list"></i>
                        </Dropdown.Toggle>
                        <Dropdown.Menu>
                            <Dropdown.Item>Disable</Dropdown.Item>
                            <Dropdown.Item>Schedule Toggle</Dropdown.Item>
                            <Dropdown.Item>Reset rule</Dropdown.Item>
                            <Dropdown.Item>Show targets</Dropdown.Item>
                            <Dropdown.Item>Debug</Dropdown.Item>
                        </Dropdown.Menu>
                    </Dropdown>
                </div>

                <Collapse in={enabled}>
                    <div className="text-center mt-3">
                        <Button
                            size="sm"
                            variant="primary"
                            className="open-rules"
                        >
                            Schedule Rules
                        </Button>
                    </div>
                </Collapse>
            </Card.Body>
        </Card>
    );
}


export default SensorCard;
