import React, { useState } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import PopupDiv from './PopupDiv';
import StandardRuleInput from 'inputs/StandardRuleInput';
import OnOffRuleInput from 'inputs/OnOffRuleInput';
import IntRangeRuleInput from 'inputs/IntRangeRuleInput';
import FloatRangeRuleInput from 'inputs/FloatRangeRuleInput';
import ThermostatRuleInput from 'inputs/ThermostatRuleInput';
import { convert_temperature } from 'util/thermostat_util';
import { get_instance_metadata } from 'util/metadata';
import { average } from 'util/helper_functions';
import { numbersOnly } from 'util/validation';

// Wrapper for slider input that adds toggle which replaces input with standard
// rule dropdown (enabled or disabled) for instances that take either rule type
const SliderRuleWrapper = ({ ruleDetails, setRuleDetails, defaultRangeRule, children }) => {
    // Toggles range_rule bool and overwrites rule with arg (needs to change to
    // enabled/disabled if toggling to false, int/float if toggling to true)
    const toggle = () => {
        setRuleDetails({
            ...ruleDetails,
            rule: ruleDetails.range_rule ? 'enabled' : defaultRangeRule,
            range_rule: !ruleDetails.range_rule
        });
    };

    return (
        <>
            {/* Slider input or enabled/disabled dropdown */}
            <div className="d-flex mt-2">
                <Form.Check
                    className="mb-3"
                    type="switch"
                    label="Range"
                    checked={ruleDetails.range_rule}
                    onChange={toggle}
                />
            </div>

            {ruleDetails.range_rule ? (
                children
            ) : (
                <StandardRuleInput
                    rule={ruleDetails.rule}
                    setRule={rule => setRuleDetails({ ...ruleDetails, rule: rule})}
                    focus={true}
                />
            )}
        </>
    );
};

SliderRuleWrapper.propTypes = {
    ruleDetails: PropTypes.object.isRequired,
    setRuleDetails: PropTypes.func.isRequired,
    defaultRangeRule: PropTypes.number.isRequired,
    children: PropTypes.node.isRequired
};

const IntOrFadeRuleInput = ({ ruleDetails, setRuleDetails, limits }) => {
    const setDuration = (duration) => {
        // Remove non-numeric, 5 digits max (longest fade = 86400 seconds)
        setRuleDetails({ ...ruleDetails,
            duration: numbersOnly(duration).substring(0,5)
        });
    };

    const setFadeToggle = () => {
        setRuleDetails({ ...ruleDetails, fade_rule: !ruleDetails.fade_rule });
    };

    return (
        <SliderRuleWrapper
            ruleDetails={ruleDetails}
            setRule={rule => setRuleDetails({ ...ruleDetails, rule: rule})}
            setRuleDetails={setRuleDetails}
            defaultRangeRule={average(limits[0], limits[1])}
        >
            <IntRangeRuleInput
                rule={ruleDetails.rule}
                setRule={rule => setRuleDetails({ ...ruleDetails, rule: rule })}
                min={parseInt(limits[0])}
                max={parseInt(limits[1])}
            />

            {ruleDetails.fade_rule ? (
                <div className={"text-center"}>
                    <Form.Label className="mt-2">Duration (seconds)</Form.Label>
                    <Form.Control
                        type="text"
                        value={ruleDetails.duration}
                        onChange={(e) => setDuration(e.target.value)}
                        autoFocus
                    />
                </div>
            ) : null}

            <div className="d-flex mt-2">
                <Form.Check
                    className="mt-3"
                    type="switch"
                    label="Fade"
                    checked={ruleDetails.fade_rule}
                    onChange={setFadeToggle}
                />
            </div>
        </SliderRuleWrapper>
    );
};

IntOrFadeRuleInput.propTypes = {
    ruleDetails: PropTypes.object.isRequired,
    setRuleDetails: PropTypes.func.isRequired,
    limits: PropTypes.array.isRequired
};

// TODO fix inconsistent type param (config = _type, API status = type) and
// remove arg (can get from instance once name consistent)
export const RuleField = ({ instance, category, type, rule, handleChange }) => {
    // Create state to control popup visibility
    const [visible, setVisible] = useState(false);

    // Get metadata for instance type (contains rule prompt)
    const metadata = get_instance_metadata(category, type);

    // Create state for rule parameters
    // - rule: Current rule value
    // - fade_rule: Controls duration field visibility
    // - duration: Current value of duration field
    // - range_rule: Show slider if true, dropdown if false
    const [ruleDetails, setRuleDetails] = useState({
        rule: rule || 'enabled',
        fade_rule: false,
        duration: 60,
        range_rule: Boolean(parseFloat(rule))
    });

    // If editing fade rule split into params, set fade_rule flag
    if (String(ruleDetails.rule).startsWith("fade")) {
        const [_, rule, duration] = String(ruleDetails.rule).split("/");
        setRuleDetails({
            ...ruleDetails,
            fade_rule: true,
            rule: rule,
            duration: duration,
            range_rule: true
        });
    }

    // Call parent handler, close popup
    const handleClose = () => {
        handleChange(
            ruleDetails.rule,
            ruleDetails.fade_rule,
            ruleDetails.duration,
            ruleDetails.range_rule
        );
        setVisible(false);
    };

    // Call parent handler, close popup if enter key pressed
    const handleEnterKey = (e) => {
        if (e.key === "Enter") {
            handleClose();
        }
    };

    return (
        <div onKeyDown={handleEnterKey}>
            {/* Display current rule, open edit popup when clicked */}
            <span
                className="form-control"
                onClick={() => setVisible(true)}
            >
                {rule ? rule : 'Set rule'}
            </span>

            {/* Edit rule popup */}
            <PopupDiv show={visible} onClose={handleClose}>
                <Form.Label>Rule</Form.Label>
                {(() => {
                    // Thermostat: Skip switch and return Float slider with temperatures converted
                    if (instance.units !== undefined) {
                        const defaultRangeRule = average(
                            convert_temperature(metadata.rule_limits[0], 'celsius', instance.units),
                            convert_temperature(metadata.rule_limits[1], 'celsius', instance.units)
                        );
                        return (
                            <SliderRuleWrapper
                                ruleDetails={ruleDetails}
                                setRule={rule => setRuleDetails({ ...ruleDetails, rule: rule})}
                                setRuleDetails={setRuleDetails}
                                defaultRangeRule={defaultRangeRule}
                            >
                                <ThermostatRuleInput
                                    rule={ruleDetails.rule}
                                    setRule={rule => setRuleDetails({ ...ruleDetails, rule: rule })}
                                    min={metadata.rule_limits[0]}
                                    max={metadata.rule_limits[1]}
                                    units={instance.units}
                                />
                            </SliderRuleWrapper>
                        );
                    }

                    // All other types: Add correct input for rule_prompt
                    switch(metadata.rule_prompt) {
                        case "standard":
                            return (
                                <StandardRuleInput
                                    rule={ruleDetails.rule}
                                    setRule={rule => setRuleDetails({ ...ruleDetails, rule: rule})}
                                    focus={true}
                                />
                            );
                        case "on_off":
                            return (
                                <OnOffRuleInput
                                    rule={ruleDetails.rule}
                                    setRule={rule => setRuleDetails({ ...ruleDetails, rule: rule})}
                                    focus={true}
                                />
                            );
                        case "float_range":
                            return (
                                <SliderRuleWrapper
                                    ruleDetails={ruleDetails}
                                    setRule={rule => setRuleDetails({ ...ruleDetails, rule: rule})}
                                    setRuleDetails={setRuleDetails}
                                    defaultRangeRule={average(
                                        metadata.rule_limits[0],
                                        metadata.rule_limits[1])
                                    }
                                >
                                    <FloatRangeRuleInput
                                        rule={ruleDetails.rule}
                                        setRule={rule => setRuleDetails({ ...ruleDetails, rule: rule })}
                                        min={metadata.rule_limits[0]}
                                        max={metadata.rule_limits[1]}
                                    />
                                </SliderRuleWrapper>
                            );
                        case "int_or_fade":
                            return (
                                <IntOrFadeRuleInput
                                    ruleDetails={ruleDetails}
                                    setRuleDetails={setRuleDetails}
                                    limits={[
                                        instance.min_rule,
                                        instance.max_rule
                                    ]}
                                />
                            );
                    }
                })()}
            </PopupDiv>
        </div>
    );
};

RuleField.propTypes = {
    instance: PropTypes.object.isRequired,
    category: PropTypes.oneOf([
        'device',
        'sensor'
    ]).isRequired,
    type: PropTypes.string.isRequired,
    rule: PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string
    ]).isRequired,
    handleChange: PropTypes.func.isRequired
};
