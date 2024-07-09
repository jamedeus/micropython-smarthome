import React from 'react';
import PropTypes from 'prop-types';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import Collapse from 'react-bootstrap/Collapse';
import ScheduleRulesTable from './ScheduleRules';
import RuleInput from './RuleInput';

const InstanceCard = ({ id, params, actionButton, dropdownOptions, setRule, onBlur=() => {} }) => {
    return (
        <Card className="mb-4">
            <Card.Body className="d-flex flex-column">
                <div className="d-flex justify-content-between">
                    {actionButton}

                    <h4 className="card-title text-center m-auto">
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
                        <RuleInput id={id} params={params} setRule={setRule} onBlur={onBlur} />

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

                        <ScheduleRulesTable id={id} schedule={params.schedule} />
                    </div>
                </Collapse>
            </Card.Body>
        </Card>
    );
};

InstanceCard.propTypes = {
    id: PropTypes.string.isRequired,
    params: PropTypes.object.isRequired,
    actionButton: PropTypes.node.isRequired,
    dropdownOptions: PropTypes.node.isRequired,
    onBlur: PropTypes.func
};

export default InstanceCard;
