import React, { useState, useContext, useEffect } from 'react';
import PropTypes from 'prop-types';
import { ApiCardContext } from 'root/ApiCardContext';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import Collapse from 'react-bootstrap/Collapse';
import RuleInput from './RuleInput';
import ScheduleRulesTable from './ScheduleRules';
import { showDebugModal } from './DebugModal';
import { showFadeModal } from './FadeModal';
import { showScheduleToggle } from './ScheduleToggleModal';
import ChangeApiTargetRule from './ChangeApiTargetRule';
import { get_instance_metadata } from 'util/metadata';
import 'css/PowerButton.css';
import 'css/TriggerButton.css';

// Top left corner of device cards
const PowerButton = ({ id, params }) => {
    const { turn_on } = useContext(ApiCardContext);

    // Create callback for power button
    const turn_on_off = () => {
        turn_on(id, !params.turned_on);
    };

    return (
        <Button
            variant="outline-primary"
            className={`power-button my-auto me-auto ${params.turned_on ? 'toggle-on' : ''}`}
            onClick={turn_on_off}
        >
            <i className="bi-lightbulb"></i>
        </Button>
    );
};

PowerButton.propTypes = {
    id: PropTypes.string.isRequired,
    params: PropTypes.object.isRequired
};

// Top left corner of sensor cards
const TriggerButton = ({ id, params, disabled }) => {
    const { trigger_sensor } = useContext(ApiCardContext);

    return (
        <Button
            variant="outline-primary"
            className={`trigger-button my-auto me-auto ${params.condition_met ? 'trigger-on' : ''}`}
            onClick={() => trigger_sensor(id)}
            disabled={disabled}
        >
            <i className="bi-exclamation-lg"></i>
        </Button>
    );
};

TriggerButton.propTypes = {
    id: PropTypes.string.isRequired,
    params: PropTypes.object.isRequired,
    disabled: PropTypes.bool.isRequired
};

const DeviceDropdownOptions = ({ id, params, rule_prompt }) => {
    const { enable_instance, reset_rule } = useContext(ApiCardContext);

    return (
        <>
            <Dropdown.Item
                onClick={() => enable_instance(id, !params.enabled)}
            >
                {params.enabled ? "Disable" : "Enable"}
            </Dropdown.Item>
            <Dropdown.Item onClick={() => showScheduleToggle(id, params.enabled)}>
                Schedule Toggle
            </Dropdown.Item>
            <Dropdown.Item
                disabled={params.current_rule === params.scheduled_rule}
                onClick={() => reset_rule(id)}
            >
                Reset rule
            </Dropdown.Item>
            {rule_prompt === "int_or_fade" ? (
                <Dropdown.Item onClick={() => showFadeModal(id)}>
                    Start Fade
                </Dropdown.Item>
            ) : ( null )}
            {params.type === "api-target" ? (
                <ChangeApiTargetRule id={id} rule={params.current_rule} />
            ) : (null) }
            <Dropdown.Item onClick={() => showDebugModal(id)}>
                Debug
            </Dropdown.Item>
        </>
    );
};

DeviceDropdownOptions.propTypes = {
    id: PropTypes.string.isRequired,
    params: PropTypes.object.isRequired,
    rule_prompt: PropTypes.string.isRequired
};

const SensorDropdownOptions = ({ id, params }) => {
    const { enable_instance, reset_rule } = useContext(ApiCardContext);

    return (
        <>
            <Dropdown.Item
                onClick={() => enable_instance(id, !params.enabled)}
            >
                {params.enabled ? "Disable" : "Enable"}
            </Dropdown.Item>
            <Dropdown.Item onClick={() => showScheduleToggle(id, params.enabled)}>
                Schedule Toggle
            </Dropdown.Item>
            <Dropdown.Item
                disabled={params.current_rule === params.scheduled_rule}
                onClick={() => reset_rule(id)}
            >
                Reset rule
            </Dropdown.Item>
            <Dropdown.Item>Show targets</Dropdown.Item>
            <Dropdown.Item onClick={() => showDebugModal(id)}>
                Debug
            </Dropdown.Item>
        </>
    );
};

SensorDropdownOptions.propTypes = {
    id: PropTypes.string.isRequired,
    params: PropTypes.object.isRequired
};

const InstanceCard = ({ id }) => {
    // Get function that returns status params, set_rule hook
    const { get_instance_section, set_rule } = useContext(ApiCardContext);

    // Get device/sensor status params, create local state
    const params = get_instance_section(id);
    const [localState, setlocalState] = useState({ ...params });

    // Create state that blocks automatic status updates while true
    const [editing, setEditing] = useState(false);

    // Update local state when upstream status changes unless user is modifying
    // inputs (apply updates immediately when editing switches back to false)
    useEffect(() => {
        if (!editing) {
            setlocalState(params);
        }
    }, [params, editing]);

    // Get metadata containing rule_prompt
    const category = id.replace(/[0-9]/g, '');
    const [metadata] = useState(
        get_instance_metadata(category, params.type)
    );

    // Rule slider handler
    const setRule = (newRule) => {
        // Prevent slider jumping if status updates while moving
        setEditing(true);
        // Set local state (move slider)
        setlocalState({ ...localState, current_rule: newRule });
        // Set upstream state (sends debounced API call to node)
        set_rule(id, newRule);
    };

    // Called when user releases click on slider, resumes status updates
    const onBlur = () => {
        setEditing(false);
    };

    return (
        <Card className="mb-4">
            <Card.Body className="d-flex flex-column">
                <div className="d-flex justify-content-between">
                    {/* Power button for devices, Trigger button for sensors */}
                    {category === 'device' ? (
                        <PowerButton id={id} params={params} />
                    ) : (
                        <TriggerButton
                            id={id}
                            params={params}
                            disabled={!metadata.triggerable}
                        />
                    )}

                    <h4 className="card-title text-center m-auto">
                        {params.nickname}
                    </h4>

                    <Dropdown align="end" className="ms-auto my-auto">
                        <Dropdown.Toggle variant="outline-secondary" className="menu-button">
                            <i className="bi-list"></i>
                        </Dropdown.Toggle>
                        <Dropdown.Menu>
                            {category === 'device' ? (
                                <DeviceDropdownOptions
                                    id={id}
                                    params={params}
                                    rule_prompt={metadata.rule_prompt}
                                />
                            ) : (
                                <SensorDropdownOptions
                                    id={id}
                                    params={params}
                                />
                            )}
                        </Dropdown.Menu>
                    </Dropdown>
                </div>

                <Collapse in={params.enabled}>
                    <div>
                        <RuleInput
                            id={id}
                            params={params}
                            setRule={setRule}
                            onBlur={onBlur}
                        />

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
    id: PropTypes.string.isRequired
};

export default InstanceCard;
