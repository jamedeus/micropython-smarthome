import React, { useState, useRef } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import PopupDiv from './PopupDiv';
import StandardRuleInput from 'inputs/StandardRuleInput';
import OnOffRuleInput from 'inputs/OnOffRuleInput';
import IntRangeRuleInput from 'inputs/IntRangeRuleInput';
import FloatRangeRuleInput from 'inputs/FloatRangeRuleInput';
import { convert_temperature } from 'util/thermostat_util';
import { get_instance_metadata } from 'util/metadata';
import { average } from 'util/helper_functions';

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
                />
            )}
        </>
    );
};

SliderRuleWrapper.propTypes = {
    ruleDetails: PropTypes.object,
    setRuleDetails: PropTypes.func,
    defaultRangeRule: PropTypes.number,
    children: PropTypes.node
};

const ThermostatRuleInput = ({ ruleDetails, setRuleDetails, units, limits }) => {
    const min = convert_temperature(limits[0], "celsius", units);
    const max = convert_temperature(limits[1], "celsius", units);

    return (
        <SliderRuleWrapper
            ruleDetails={ruleDetails}
            setRule={rule => setRuleDetails({ ...ruleDetails, rule: rule})}
            setRuleDetails={setRuleDetails}
            defaultRangeRule={average(min, max)}
        >
            <FloatRangeRuleInput
                rule={ruleDetails.rule}
                setRule={rule => setRuleDetails({ ...ruleDetails, rule: rule })}
                min={min}
                max={max}
                sliderStep={0.1}
            />
        </SliderRuleWrapper>
    );
};

ThermostatRuleInput.propTypes = {
    ruleDetails: PropTypes.object,
    setRuleDetails: PropTypes.func,
    units: PropTypes.string,
    limits: PropTypes.array
};

const IntOrFadeRuleInput = ({ ruleDetails, setRuleDetails, limits }) => {
    const setDuration = (duration) => {
        setRuleDetails({ ...ruleDetails, duration: duration});
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

            <div className={ruleDetails.fade_rule ? "text-center" : "d-none"}>
                <Form.Label className="mt-2">Duration (seconds)</Form.Label>
                <Form.Control
                    type="text"
                    value={ruleDetails.duration}
                    onChange={(e) => setDuration(e.target.value)}
                />
            </div>

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
    ruleDetails: PropTypes.object,
    setRuleDetails: PropTypes.func,
    limits: PropTypes.array
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
        rule: rule,
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

    // Reference to span that shows current rule, opens popup
    const buttonRef = useRef(null);

    return (
        <div>
            {/* Display current rule, open edit popup when clicked */}
            <span
                ref={buttonRef}
                className="form-control"
                onClick={() => setVisible(true)}
            >
                {rule ? rule : 'Set rule'}
            </span>

            {/* Edit rule popup */}
            <PopupDiv show={visible} anchorRef={buttonRef} onClose={handleClose}>
                <Form.Label>Rule</Form.Label>
                {(() => {
                    // Thermostat: Skip switch and return Float slider with temperatures converted
                    if (metadata && metadata.config_template.units !== undefined) {
                        return (
                            <ThermostatRuleInput
                                ruleDetails={ruleDetails}
                                setRuleDetails={setRuleDetails}
                                units={instance.units}
                                limits={metadata.rule_limits}
                            />
                        );
                    }

                    // All other types: Add correct input for rule_prompt
                    switch(metadata.rule_prompt) {
                        case "standard":
                            return (
                                <StandardRuleInput
                                    rule={ruleDetails.rule}
                                    setRule={rule => setRuleDetails({ ...ruleDetails, rule: rule})}
                                />
                            );
                        case "on_off":
                            return (
                                <OnOffRuleInput
                                    rule={ruleDetails.rule}
                                    setRule={rule => setRuleDetails({ ...ruleDetails, rule: rule})}
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
    instance: PropTypes.object,
    category: PropTypes.oneOf([
        'device',
        'sensor'
    ]),
    type: PropTypes.string,
    timestamp: PropTypes.string,
    rule: PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string
    ]),
    handleChange: PropTypes.func
};
