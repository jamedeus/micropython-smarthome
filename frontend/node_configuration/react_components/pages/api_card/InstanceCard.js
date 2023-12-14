import React from 'react';
import PropTypes from 'prop-types';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import Collapse from 'react-bootstrap/Collapse';
import { ScheduleRulesTable } from './ScheduleRules';
import RuleInput from './RuleInput';


const InstanceCard = ({ id, params, actionButton, dropdownOptions }) => {
    return (
        <Card className="mb-4">
            <Card.Body className="d-flex flex-column">
                <div className="d-flex justify-content-between">
                    {actionButton}

                    <h4 className="card-title mx-auto my-auto">
                        {params.nickname}
                    </h4>

                    <Dropdown align="end" className="ms-auto my-auto">
                        <Dropdown.Toggle variant="outline-secondary" className="menu-button">
                            <i className="bi-list"></i>
                        </Dropdown.Toggle>
                        <Dropdown.Menu>
                            {dropdownOptions}
                        </Dropdown.Menu>
                    </Dropdown>
                </div>

                <Collapse in={params.enabled}>
                    <div>
                        {/* BUG if device is disabled this will pass string to rule slider current_rule */}
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

InstanceCard.propTypes = {
    id: PropTypes.string,
    params: PropTypes.object,
    actionButton: PropTypes.node,
    dropdownOptions: PropTypes.node
};


export default InstanceCard;
