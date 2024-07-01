import React, { useState, useRef, useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from 'root/ConfigContext';
import Form from 'react-bootstrap/Form';
import PopupDiv from './PopupDiv';
import StandardRuleInput from 'inputs/StandardRuleInput';
import OnOffRuleInput from 'inputs/OnOffRuleInput';
import IntRangeRuleInput from 'inputs/IntRangeRuleInput';
import FloatRangeRuleInput from 'inputs/FloatRangeRuleInput';
import { convert_temperature } from 'util/thermostat_util';
import { get_instance_metadata } from 'util/metadata';

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
            setRule={rule => setRuleDetails({ ...ruleDetails, rule: rule})}
            setRuleDetails={setRuleDetails}
            defaultRangeRule={defaultRangeRule}
        >
            <FloatRangeRuleInput
                rule={ruleDetails.rule}
                setRule={rule => setRuleDetails({ ...ruleDetails, rule: rule })}
                min={convert_temperature(limits[0], "celsius", units)}
                max={convert_temperature(limits[1], "celsius", units)}
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
            defaultRangeRule={parseInt(parseInt(limits[1]) / 2)}
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
                                    setRuleDetails={setRuleDetails}
                                    units={config[instance]["units"]}
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
                                        defaultRangeRule={parseInt(parseInt(metadata.rule_limits[1]) / 2)}
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
                                            config[instance]["min_rule"],
                                            config[instance]["max_rule"]
                                        ]}
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
