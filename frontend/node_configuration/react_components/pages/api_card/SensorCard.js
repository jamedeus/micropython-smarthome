import React, { useState, useContext } from 'react';
import PropTypes from 'prop-types';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import Collapse from 'react-bootstrap/Collapse';
import { ScheduleRulesTable } from './ScheduleRules';
import RuleInput from './RuleInput';
import { ApiCardContext } from 'root/ApiCardContext';
import 'css/TriggerButton.css';


const TriggerButton = ({ on, onClick }) => {
    return (
        <Button
            variant="outline-primary"
            className={on ? "trigger-button my-auto me-auto trigger-on" : "trigger-button my-auto me-auto"}
            onClick={onClick}
        >
            <i className="bi-exclamation-lg"></i>
        </Button>
    );
}


const SensorCard = ({ id }) => {
    // Get status object
    const {status, enable_instance, trigger_sensor, reset_rule} = useContext(ApiCardContext);
    const params = status["sensors"][id];

    // Create state for trigger button
    const [triggered, setTriggered] = useState(false);

    let category;
    if (id.startsWith("device")) {
        category = "devices";
    } else {
        category = "sensors";
    }

    const trigger = () => {
        trigger_sensor(id);
    };

    return (
        <Card className="mb-4">
            <Card.Body className="d-flex flex-column">
                <div className="d-flex justify-content-between">
                    <TriggerButton on={params.condition_met} onClick={trigger} />

                    <h4 className="card-title mx-auto my-auto">
                        {params.nickname}
                    </h4>

                    <Dropdown align="end" className="ms-auto my-auto">
                        <Dropdown.Toggle variant="outline-secondary" className="menu-button">
                            <i className="bi-list"></i>
                        </Dropdown.Toggle>
                        <Dropdown.Menu>
                            <Dropdown.Item
                                onClick={() => enable_instance(id, category, !params.enabled)}
                            >
                                {params.enabled ? "Disable" : "Enable"}
                            </Dropdown.Item>
                            <Dropdown.Item>Schedule Toggle</Dropdown.Item>
                            <Dropdown.Item
                                disabled={params.current_rule === params.scheduled_rule}
                                onClick={() => reset_rule(id)}
                            >
                                Reset rule
                            </Dropdown.Item>
                            <Dropdown.Item>Show targets</Dropdown.Item>
                            <Dropdown.Item>Debug</Dropdown.Item>
                        </Dropdown.Menu>
                    </Dropdown>
                </div>

                <Collapse in={params.enabled}>
                    <div>
                        {/* BUG if sensor is disabled this will pass string to rule slider current_rule */}
                        {/* Renders slider with NaN, broken until next status update after enabling card */}
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

SensorCard.propTypes = {
    id: PropTypes.string
};


export default SensorCard;
