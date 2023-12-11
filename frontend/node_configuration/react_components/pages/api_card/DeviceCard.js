import React, { useState, useContext, useEffect } from 'react';
import PropTypes from 'prop-types';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import Collapse from 'react-bootstrap/Collapse';
import { ScheduleRulesTable } from './ScheduleRules';
import RuleInput from './RuleInput';
import { ApiCardContext } from 'root/ApiCardContext';


const DeviceCard = ({ id }) => {
    // Get status object
    const {status} = useContext(ApiCardContext);
    const params = status["devices"][id];

    // Create state for trigger button
    const [powerState, setPowerState] = useState(false);

    // Create state for enable status (controls card collapse)
    const [enabled, setEnabled] = useState(params.enabled);

    // Create state for schedule rules section collapse
    const [rulesOpen, setRulesOpen] = useState(false);

    // Update enabled state when param changes
    useEffect(() => {
        setEnabled(params.enabled);
    }, [params.enabled]);

    return (
        <Card className="mb-4">
            <Card.Body className="d-flex flex-column">
                <div className="d-flex justify-content-between">
                    <Button
                        variant="outline-primary"
                        className="power-button my-auto me-auto"
                    >
                        <i className="bi-lightbulb"></i>
                    </Button>

                    <h4 className="card-title mx-auto my-auto">
                        {params.nickname}
                    </h4>

                    <Dropdown align="end" className="ms-auto my-auto">
                        <Dropdown.Toggle variant="outline-secondary" className="menu-button">
                            <i className="bi-list"></i>
                        </Dropdown.Toggle>
                        <Dropdown.Menu>
                            <Dropdown.Item onClick={() => setEnabled(!enabled)}>Disable</Dropdown.Item>
                            <Dropdown.Item>Schedule Toggle</Dropdown.Item>
                            <Dropdown.Item>Reset rule</Dropdown.Item>
                            <Dropdown.Item>Debug</Dropdown.Item>
                        </Dropdown.Menu>
                    </Dropdown>
                </div>

                <Collapse in={enabled}>
                    <div>
                        <RuleInput id={id} params={params} />

                        <div className="text-center my-3">
                            <Button
                                size="sm"
                                variant="primary"
                                className="open-rules"
                                data-bs-toggle="collapse"
                                data-bs-target={`#${id}-schedule-rules`}
                            >
                                Schedule rules
                            </Button>
                        </div>

                        <div className="collapse text-center" id={`${id}-schedule-rules`}>
                            <ScheduleRulesTable id={id} schedule={params.schedule} />

                            <div className="text-center mx-3 mb-3">
                                <Button variant="secondary" size="sm">
                                    <i className="bi-plus-lg"></i>
                                </Button>
                            </div>
                        </div>
                    </div>
                </Collapse>
            </Card.Body>
        </Card>
    );
};

DeviceCard.propTypes = {
    id: PropTypes.string
};


export default DeviceCard;
