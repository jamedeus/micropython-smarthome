import React, { useState, useRef, useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from 'root/ConfigContext';
import Form from 'react-bootstrap/Form';
import PopupDiv from './PopupDiv';
import Dropdown from 'inputs/Dropdown.js';
import RuleSlider from 'inputs/RuleSlider';
import { convert_temperature } from 'util/thermostat_util';
import { get_instance_metadata } from 'util/metadata';

const StandardRuleInput = ({ rule, setRule }) => {
    return (
        <Dropdown
            value={rule}
            options={["Enabled", "Disabled"]}
            onChange={(value) => setRule(value)}
        />
    );
};

StandardRuleInput.propTypes = {
    rule: PropTypes.string,
    setRule: PropTypes.func
};

const OnOffRuleInput = ({ rule, setRule }) => {
    return (
        <Dropdown
            value={rule}
            options={["Enabled", "Disabled", "On", "Off"]}
            onChange={(value) => setRule(value)}
        />
    );
};

OnOffRuleInput.propTypes = {
    rule: PropTypes.string,
    setRule: PropTypes.func
};

// Wrapper for slider input that adds toggle which replaces input with standard
// rule dropdown (enabled or disabled) for instances that take either rule type
const SliderRuleWrapper = ({
    ruleDetails,
    setRule,
    toggleRangeRule,
    defaultRangeRule,
    children
}) => {
    // Set rule to enabled if switching to dropdown, number if switching to slider
    const toggle = () => {
        toggleRangeRule(ruleDetails.range_rule ? 'enabled' : defaultRangeRule);
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
                    setRule={setRule}
                />
            )}
        </>
    );
};

SliderRuleWrapper.propTypes = {
    ruleDetails: PropTypes.object,
    setRule: PropTypes.func,
    toggleRangeRule: PropTypes.func,
    defaultRangeRule: PropTypes.number,
    children: PropTypes.node
};

// Handler for slider + and - buttons
const handleButtonClick = (rule, step, direction, min_rule, max_rule) => {
    let new_rule;
    if (direction === "up") {
        new_rule = parseFloat(rule) + parseFloat(step);
    } else {
        new_rule = parseFloat(rule) - parseFloat(step);
    }

    // Enforce rule limits
    if (new_rule < parseFloat(min_rule)) {
        new_rule = parseFloat(min_rule);
    } else if (new_rule > parseFloat(max_rule)) {
        new_rule = parseFloat(max_rule);
    }

    return new_rule;
};

const ThermostatRuleInput = ({ ruleDetails, units, limits, setRule, toggleRangeRule }) => {
    const onButtonClick = (step, direction, min_rule, max_rule) => {
        const newRule = handleButtonClick(ruleDetails.rule, step, direction, min_rule, max_rule);
        setRule(newRule);
    };

    // Default rule when changing from dropdown to slider
    let defaultRangeRule;
    switch(units) {
        case('celsius'):
            defaultRangeRule = 22;
            break;
        case('fahrenheit'):
            defaultRangeRule = 71;
            break;
        case('kelvin'):
            defaultRangeRule = 295;
            break;
    }

    return (
        <SliderRuleWrapper
            ruleDetails={ruleDetails}
            setRule={setRule}
            toggleRangeRule={toggleRangeRule}
            defaultRangeRule={defaultRangeRule}
        >
            <RuleSlider
                rule_value={ruleDetails.rule}
                slider_min={convert_temperature(limits[0], "celsius", units)}
                slider_max={convert_temperature(limits[1], "celsius", units)}
                slider_step={0.1}
                button_step={0.5}
                display_type={"float"}
                onButtonClick={onButtonClick}
                onSliderMove={setRule}
            />
        </SliderRuleWrapper>
    );
};

ThermostatRuleInput.propTypes = {
    ruleDetails: PropTypes.object,
    units: PropTypes.string,
    limits: PropTypes.array,
    setRule: PropTypes.func,
    toggleRangeRule: PropTypes.func
};

const FloatRangeRuleInput = ({ ruleDetails, limits, setRule, toggleRangeRule }) => {
    const onButtonClick = (step, direction, min_rule, max_rule) => {
        const newRule = handleButtonClick(ruleDetails.rule, step, direction, min_rule, max_rule);
        setRule(newRule);
    };

    return (
        <SliderRuleWrapper
            ruleDetails={ruleDetails}
            setRule={setRule}
            toggleRangeRule={toggleRangeRule}
            defaultRangeRule={parseInt(parseInt(limits[1]) / 2)}
        >
            <RuleSlider
                rule_value={ruleDetails.rule}
                slider_min={limits[0]}
                slider_max={limits[1]}
                slider_step={0.5}
                button_step={0.5}
                display_type={"float"}
                onButtonClick={onButtonClick}
                onSliderMove={setRule}
            />
        </SliderRuleWrapper>
    );
};

FloatRangeRuleInput.propTypes = {
    ruleDetails: PropTypes.object,
    limits: PropTypes.array,
    setRule: PropTypes.func,
    toggleRangeRule: PropTypes.func
};

const IntOrFadeRuleInput = ({ ruleDetails, limits, setRule, setRuleParam, toggleRangeRule }) => {
    const onButtonClick = (step, direction, min_rule, max_rule) => {
        const newRule = handleButtonClick(ruleDetails.rule, step, direction, min_rule, max_rule);
        setRule(newRule);
    };

    return (
        <SliderRuleWrapper
            ruleDetails={ruleDetails}
            setRule={setRule}
            toggleRangeRule={toggleRangeRule}
            defaultRangeRule={parseInt(parseInt(limits[1]) / 2)}
        >
            <RuleSlider
                rule_value={parseInt(ruleDetails.rule)}
                slider_min={parseInt(limits[0])}
                slider_max={parseInt(limits[1])}
                slider_step={1}
                button_step={1}
                display_type={"int"}
                onButtonClick={onButtonClick}
                onSliderMove={setRule}
            />

            <div className={ruleDetails.fade_rule ? "text-center" : "d-none"}>
                <Form.Label className="mt-2">Duration (seconds)</Form.Label>
                <Form.Control
                    type="text"
                    value={ruleDetails.duration}
                    onChange={(e) => setRuleParam("duration", e.target.value)}
                />
            </div>

            <div className="d-flex mt-2">
                <Form.Check
                    className="mt-3"
                    type="switch"
                    label="Fade"
                    checked={ruleDetails.fade_rule}
                    onChange={(e) => setRuleParam("fade_rule", e.target.checked)}
                />
            </div>
        </SliderRuleWrapper>
    );
};

IntOrFadeRuleInput.propTypes = {
    ruleDetails: PropTypes.object,
    limits: PropTypes.array,
    setRule: PropTypes.func,
    setRuleParam: PropTypes.func,
    toggleRangeRule: PropTypes.func
};

export const RuleField = ({ instance, timestamp }) => {
    // Get curent state from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Create state to control popup visibility
    const [visible, setVisible] = useState(false);

    // Get metadata for instance type (contains rule prompt)
    const category = instance.replace(/[0-9]/g, '');
    const metadata = get_instance_metadata(category, config[instance]["_type"]);

    // Create state for rule parameters
    // - rule: Current rule value
    // - fade_rule: Controls duration field visibility
    // - duration: Current value of duration field
    // - range_rule: Show slider if true, dropdown if false
    const [ruleDetails, setRuleDetails] = useState({
        rule: config[instance]["schedule"][timestamp],
        fade_rule: false,
        duration: 60,
        range_rule: Boolean(parseFloat(config[instance]["schedule"][timestamp]))
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

    const handleClose = () => {
        // Get existing schedule rules
        const rules = config[instance]["schedule"];

        // Add new/modified rule to existing rules
        if (ruleDetails.range_rule && ruleDetails.fade_rule) {
            // Fade rule: Combine params into single string
            rules[timestamp] = `fade/${ruleDetails.rule}/${ruleDetails.duration}`;
        } else {
            rules[timestamp] = ruleDetails.rule;
        }

        // Update state, close modal
        handleInputChange(instance, "schedule", rules);
        setVisible(false);
    };

    // Takes ruleDetails param name and value, updates and re-renders
    const setRuleParam = (param, value) => {
        setRuleDetails({ ...ruleDetails, [param]: value});
    };

    // Handler for slider move events
    const setRule = (value) => {
        setRuleDetails({ ...ruleDetails, ["rule"]: value});
    };

    // Toggles range_rule bool and overwrites rule with arg (needs to change to
    // enabled/disabled if toggling to false, int/float if toggling to true)
    const toggleRangeRule = (newRule) => {
        setRuleDetails({
            ...ruleDetails,
            rule: newRule,
            range_rule: !ruleDetails.range_rule
        });
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
                {config[instance]["schedule"][timestamp]}
            </span>

            {/* Edit rule popup */}
            <PopupDiv show={visible} anchorRef={buttonRef} onClose={handleClose}>
                <>
                    <Form.Label>Rule</Form.Label>
                    {(() => {
                        // Thermostat: Skip switch and return Float slider with temperatures converted
                        if (metadata && metadata.config_template.units !== undefined) {
                            return (
                                <ThermostatRuleInput
                                    ruleDetails={ruleDetails}
                                    units={config[instance]["units"]}
                                    limits={metadata.rule_limits}
                                    setRule={setRule}
                                    toggleRangeRule={toggleRangeRule}
                                />
                            );
                        }

                        // All other types: Add correct input for rule_prompt
                        switch(metadata.rule_prompt) {
                            case "standard":
                                return (
                                    <StandardRuleInput
                                        rule={ruleDetails.rule}
                                        setRule={setRule}
                                    />
                                );
                            case "on_off":
                                return (
                                    <OnOffRuleInput
                                        rule={ruleDetails.rule}
                                        setRule={setRule}
                                    />
                                );
                            case "float_range":
                                return (
                                    <FloatRangeRuleInput
                                        ruleDetails={ruleDetails}
                                        limits={metadata.rule_limits}
                                        setRule={setRule}
                                        toggleRangeRule={toggleRangeRule}
                                    />
                                );
                            case "int_or_fade":
                                return (
                                    <IntOrFadeRuleInput
                                        ruleDetails={ruleDetails}
                                        limits={[
                                            config[instance]["min_rule"],
                                            config[instance]["max_rule"]
                                        ]}
                                        setRule={setRule}
                                        setRuleParam={setRuleParam}
                                        toggleRangeRule={toggleRangeRule}
                                    />
                                );
                        }
                    })()}
                </>
            </PopupDiv>
        </div>
    );
};

RuleField.propTypes = {
    instance: PropTypes.string,
    timestamp: PropTypes.string
};
