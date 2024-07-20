import React, { useState, useContext, useEffect } from 'react';
import PropTypes from 'prop-types';
import { ApiCardContext } from 'root/ApiCardContext';
import { MetadataContext } from 'root/MetadataContext';
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
import ClimateDataCard from './ClimateDataCard';
import { CSSTransition } from 'react-transition-group';
import 'css/api_card_buttons.css';

// Top left corner of device cards
const PowerButton = ({ id, params }) => {
    const { turn_on } = useContext(ApiCardContext);

    // Create callback for power button
    const turn_on_off = () => {
        turn_on(id, !params.turned_on);
    };

    return (
        <CSSTransition
            in={params.turned_on && params.enabled}
            timeout={1200}
            classNames='btn-active'
            appear
        >
            <Button
                variant="outline-secondary"
                className="power-button my-auto me-auto"
                onClick={turn_on_off}
            >
                <i className="bi-lightbulb"></i>
            </Button>
        </CSSTransition>
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
        <CSSTransition
            in={params.condition_met && params.enabled}
            timeout={1200}
            classNames='btn-active'
            appear
        >
            <Button
                variant="outline-secondary"
                className="trigger-button my-auto me-auto"
                onClick={() => trigger_sensor(id)}
                disabled={disabled}
            >
                <i className="bi-exclamation-lg"></i>
            </Button>
        </CSSTransition>
    );
};

TriggerButton.propTypes = {
    id: PropTypes.string.isRequired,
    params: PropTypes.object.isRequired,
    disabled: PropTypes.bool.isRequired
};

const DeviceDropdownOptions = ({ id, params, rule_prompt }) => {
    return (
        <>
            {rule_prompt === "int_or_fade" ? (
                <Dropdown.Item onClick={() => showFadeModal(id)}>
                    Start Fade
                </Dropdown.Item>
            ) : ( null )}
            {params.type === "api-target" ? (
                <ChangeApiTargetRule id={id} rule={params.current_rule} />
            ) : (null) }
        </>
    );
};

DeviceDropdownOptions.propTypes = {
    id: PropTypes.string.isRequired,
    params: PropTypes.object.isRequired,
    rule_prompt: PropTypes.string.isRequired
};

const SensorDropdownOptions = ({ id }) => {
    const { show_targets } = useContext(ApiCardContext);

    return (
        <Dropdown.Item onClick={() => show_targets(id)}>
            Show targets
        </Dropdown.Item>
    );
};

SensorDropdownOptions.propTypes = {
    id: PropTypes.string.isRequired
};

const InstanceCard = ({ id }) => {
    // Get function that returns status params, hooks to send API calls
    const {
        recording,
        get_instance_section,
        debounced_set_rule,
        enable_instance,
        reset_rule,
        highlightCards
    } = useContext(ApiCardContext);

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
    const { get_instance_metadata } = useContext(MetadataContext);
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
        debounced_set_rule(id, newRule);
    };

    // Called when user releases click on slider, resumes status updates
    const onBlur = () => {
        setEditing(false);
    };

    // Enable/Disable dropdown option handler
    const enable = () => {
        enable_instance(id, !localState.enabled);
    };

    // Schedule toggle dropdown option handler
    const scheduleToggle = () => {
        showScheduleToggle(id, localState.enabled);
    };

    return (
        <>
            {/* Add separate climate data card for temperature sensors */}
            {["si7021", "dht22"].includes(params.type) ? (
                <ClimateDataCard
                    temperature={parseFloat(params.temp).toFixed(2)}
                    humidity={parseFloat(params.humid).toFixed(2)}
                />
            ) : null}

            <CSSTransition
                in={highlightCards.includes(id)}
                timeout={1000}
                classNames='highlight'
            >

                <Card className="mb-4">
                    <Card.Body className="d-flex flex-column">
                        <div className="d-flex justify-content-between">
                            {/* Top left corner button */}
                            {category === 'device' ? (
                                <PowerButton id={id} params={localState} />
                            ) : (
                                <TriggerButton
                                    id={id}
                                    params={localState}
                                    disabled={!metadata.triggerable}
                                />
                            )}

                            {/* Title */}
                            <h4 className="card-title text-center m-auto">
                                {localState.nickname}
                            </h4>

                            {/* Top right corner dropdown menu */}
                            <Dropdown align="end" className="ms-auto my-auto">
                                <Dropdown.Toggle
                                    variant="outline-secondary"
                                    className="menu-button"
                                >
                                    <i className="bi-list"></i>
                                </Dropdown.Toggle>
                                <Dropdown.Menu>
                                    <Dropdown.Item onClick={enable}>
                                        {localState.enabled ? "Disable" : "Enable"}
                                    </Dropdown.Item>
                                    <Dropdown.Item onClick={scheduleToggle}>
                                        Schedule Toggle
                                    </Dropdown.Item>
                                    <Dropdown.Item
                                        disabled={localState.current_rule === localState.scheduled_rule}
                                        onClick={() => reset_rule(id)}
                                    >
                                        Reset rule
                                    </Dropdown.Item>
                                    {category === 'device' ? (
                                        <DeviceDropdownOptions
                                            id={id}
                                            params={localState}
                                            rule_prompt={metadata.rule_prompt}
                                        />
                                    ) : (
                                        <SensorDropdownOptions id={id} />
                                    )}
                                    <Dropdown.Item onClick={() => showDebugModal(id)}>
                                        Debug
                                    </Dropdown.Item>
                                </Dropdown.Menu>
                            </Dropdown>
                        </div>

                        {/* Card body (collapses while disabled */}
                        <Collapse in={localState.enabled}>
                            <div>
                                <RuleInput
                                    id={id}
                                    params={localState}
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
                                        disabled={recording ? true : false}
                                    >
                                        Schedule rules
                                    </Button>
                                </div>

                                <ScheduleRulesTable
                                    id={id}
                                    instance={localState}
                                />
                            </div>
                        </Collapse>
                    </Card.Body>
                </Card>
            </CSSTransition>
        </>
    );
};

InstanceCard.propTypes = {
    id: PropTypes.string.isRequired
};

export default InstanceCard;
