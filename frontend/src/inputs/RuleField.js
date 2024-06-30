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

const ThermostatRuleInput = ({ rule, units, limits, onButtonClick, setRule }) => {
    return (
        <RuleSlider
            rule_value={rule}
            slider_min={convert_temperature(limits[0], "celsius", units)}
            slider_max={convert_temperature(limits[1], "celsius", units)}
            slider_step={0.1}
            button_step={0.5}
            display_type={"float"}
            onButtonClick={onButtonClick}
            onSliderMove={setRule}
        />
    );
};

ThermostatRuleInput.propTypes = {
    rule: PropTypes.number,
    units: PropTypes.string,
    limits: PropTypes.array,
    onButtonClick: PropTypes.func,
    setRule: PropTypes.func
};

const FloatRangeRuleInput = ({ rule, limits, onButtonClick, setRule }) => {
    return (
        <RuleSlider
            rule_value={rule}
            slider_min={limits[0]}
            slider_max={limits[1]}
            slider_step={0.5}
            button_step={0.5}
            display_type={"float"}
            onButtonClick={onButtonClick}
            onSliderMove={setRule}
        />
    );
};

FloatRangeRuleInput.propTypes = {
    rule: PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string
    ]),
    limits: PropTypes.array,
    onButtonClick: PropTypes.func,
    setRule: PropTypes.func
};

const IntOrFadeRuleInput = ({ rule, fade, duration, limits, onButtonClick, setRule, set_popup_param }) => {
    return (
        <>
            <RuleSlider
                rule_value={parseInt(rule)}
                slider_min={parseInt(limits[0])}
                slider_max={parseInt(limits[1])}
                slider_step={1}
                button_step={1}
                display_type={"int"}
                onButtonClick={onButtonClick}
                onSliderMove={setRule}
            />

            {/* Fade duration input */}
            <div className={fade ? "text-center" : "d-none"}>
                <Form.Label className="mt-2">Duration (seconds)</Form.Label>
                <Form.Control
                    type="text"
                    value={duration}
                    onChange={(e) => set_popup_param("duration", e.target.value)}
                />
            </div>

            {/* Fade mode */}
            <div className="d-flex mt-2">
                <Form.Check
                    id="fade-switch"
                    type="switch"
                    label="Fade"
                    checked={fade}
                    onChange={(e) => set_popup_param("fade_rule", e.target.checked)}
                />
            </div>
        </>
    );
};

IntOrFadeRuleInput.propTypes = {
    rule: PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string
    ]),
    fade: PropTypes.bool,
    duration: PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string
    ]),
    limits: PropTypes.array,
    onButtonClick: PropTypes.func,
    setRule: PropTypes.func,
    set_popup_param: PropTypes.func
};

export const RuleField = ({ instance, timestamp }) => {
    // Get curent state from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Create state for popup visibility, contents
    const [popupContent, setPopupContent] = useState({
        visible: false,
        instance: '',
        timestamp: '',
        rule: '',
        fade_rule: false,
        duration: '',
        metadata: ''
    });

    const handleShow = (timestamp) => {
        // Get metadata for selected instance type (contains rule prompt)
        const category = instance.replace(/[0-9]/g, '');
        const metadata = get_instance_metadata(category, config[instance]["_type"]);

        // Replace popupContent with params for selected rule
        let update = {
            visible: true,
            instance: instance,
            timestamp: timestamp,
            rule: config[instance]["schedule"][timestamp],
            fade_rule: false,
            metadata: metadata
        };

        // If editing fade rule split into params, set fade_rule flag
        if (String(update.rule).startsWith("fade")) {
            const [_, rule, duration] = String(update.rule).split("/");
            update.fade_rule = true;
            update.duration = duration;
            update.rule = rule;
        // Otherwise set 60 second placeholder (default if user toggles fade)
        } else {
            update.duration = 60;
        }

        // Set modal contents, show
        setPopupContent(update);
    };

    const handleClose = () => {
        // Get existing rules
        const rules = config[popupContent.instance]["schedule"];

        // Get new rule from modal contents
        let new_rule;
        if (popupContent.fade_rule) {
            // Fade rule: Combine params into single string
            new_rule = `fade/${popupContent.rule}/${popupContent.duration}`;
        } else {
            new_rule = popupContent.rule;
        }

        // Add new rule, update state object, close modal
        rules[popupContent.timestamp] = new_rule;
        handleInputChange(popupContent.instance, "schedule", rules);
        setPopupContent({ ...popupContent, ["visible"]: false});
    };

    // Takes popupContent param name and value, updates and re-renders
    const set_popup_param = (param, value) => {
        setPopupContent({ ...popupContent, [param]: value});
    };

    // Handler for slider move events
    const setRule = (value) => {
        setPopupContent({ ...popupContent, ["rule"]: value});
    };

    // Handler for slider + and - buttons
    const onButtonClick = (step, direction, min_rule, max_rule) => {
        let new_rule;
        if (direction === "up") {
            new_rule = parseFloat(popupContent.rule) + parseFloat(step);
        } else {
            new_rule = parseFloat(popupContent.rule) - parseFloat(step);
        }

        // Enforce rule limits
        if (new_rule < parseFloat(min_rule)) {
            new_rule = parseFloat(min_rule);
        } else if (new_rule > parseFloat(max_rule)) {
            new_rule = parseFloat(max_rule);
        }

        setPopupContent({ ...popupContent, ["rule"]: new_rule});
    };

    // Reference to span that shows current rule, opens popup
    const buttonRef = useRef(null);

    return (
        <div>
            {/* Display current rule, open edit popup when clicked */}
            <span
                ref={buttonRef}
                className="form-control"
                onClick={() => handleShow(timestamp)}
            >
                {config[instance]["schedule"][timestamp]}
            </span>

            {/* Edit rule popup */}
            <PopupDiv show={popupContent.visible} anchorRef={buttonRef} onClose={handleClose}>
                <>
                    <Form.Label>Rule</Form.Label>
                    {(() => {
                        // Thermostat: Skip switch and return Float slider with temperatures converted
                        if (popupContent.metadata && popupContent.metadata.config_template.units !== undefined) {
                            return (
                                <ThermostatRuleInput
                                    rule={popupContent.rule}
                                    units={config[instance]["units"]}
                                    limits={popupContent.metadata.rule_limits}
                                    onButtonClick={onButtonClick}
                                    setRule={setRule}
                                />
                            );
                        }

                        // All other types: Add correct input for rule_prompt
                        switch(popupContent.metadata.rule_prompt) {
                            case "standard":
                                return (
                                    <StandardRuleInput
                                        rule={popupContent.rule}
                                        setRule={setRule}
                                    />
                                );
                            case "on_off":
                                return (
                                    <OnOffRuleInput
                                        rule={popupContent.rule}
                                        setRule={setRule}
                                    />
                                );
                            case "float_range":
                                return (
                                    <FloatRangeRuleInput
                                        rule={popupContent.rule}
                                        limits={popupContent.metadata.rule_limits}
                                        onButtonClick={onButtonClick}
                                        setRule={setRule}
                                    />
                                );
                            case "int_or_fade":
                                return (
                                    <IntOrFadeRuleInput
                                        rule={popupContent.rule}
                                        fade={popupContent.fade_rule}
                                        duration={popupContent.duration}
                                        limits={[
                                            config[popupContent.instance]["min_rule"],
                                            config[popupContent.instance]["max_rule"]
                                        ]}
                                        onButtonClick={onButtonClick}
                                        setRule={setRule}
                                        set_popup_param={set_popup_param}
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
