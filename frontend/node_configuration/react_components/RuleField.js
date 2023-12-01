import React, { useState, useRef, useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from './ConfigContext';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import PopupDiv from './PopupDiv';
import Dropdown from './inputs/Dropdown.js';
import RuleSlider from './inputs/RuleSlider';
import { convert_temperature } from './thermostat_util';
import { get_instance_metadata } from './metadata';

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
    const onSliderMove = (value) => {
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
            <span ref={buttonRef} className="form-control" onClick={() => handleShow(timestamp)}>
                {config[instance]["schedule"][timestamp]}
            </span>

            {/* Edit rule popup */}
            <PopupDiv show={popupContent.visible} anchorRef={buttonRef} onClose={handleClose}>
                <>
                    <Form.Label>Rule</Form.Label>
                    {(() => {
                        // Thermostat: Skip switch and return Float slider with temperatures converted
                        if (popupContent.metadata && popupContent.metadata.config_template.units !== undefined) {
                            const rule_limits = popupContent.metadata.rule_limits;
                            const units = config[instance]["units"];
                            return (
                                <RuleSlider
                                    rule_value={popupContent.rule}
                                    slider_min={convert_temperature(rule_limits[0], "celsius", units)}
                                    slider_max={convert_temperature(rule_limits[1], "celsius", units)}
                                    slider_step={0.1}
                                    button_step={0.5}
                                    display_type={"float"}
                                    onButtonClick={onButtonClick}
                                    onSliderMove={onSliderMove}
                                />
                            );
                        }

                        // All other types: Add correct input for rule_prompt
                        switch(popupContent.metadata.rule_prompt) {
                            case "standard":
                                return (
                                    <Dropdown
                                        value={popupContent.rule}
                                        options={["Enabled", "Disabled"]}
                                        onChange={(value) => set_popup_param("rule", value)}
                                    />
                                );
                            case "on_off":
                                return (
                                    <Dropdown
                                        value={popupContent.rule}
                                        options={["Enabled", "Disabled", "On", "Off"]}
                                        onChange={(value) => set_popup_param("rule", value)}
                                    />
                                );
                            case "float_range":
                                return (
                                    <RuleSlider
                                        rule_value={popupContent.rule}
                                        slider_min={popupContent.metadata.rule_limits[0]}
                                        slider_max={popupContent.metadata.rule_limits[1]}
                                        slider_step={0.5}
                                        button_step={0.5}
                                        display_type={"float"}
                                        onButtonClick={onButtonClick}
                                        onSliderMove={onSliderMove}
                                    />
                                );
                            case "int_or_fade":
                                return (
                                    <>
                                        <RuleSlider
                                            rule_value={parseInt(popupContent.rule)}
                                            slider_min={parseInt(config[popupContent.instance]["min_rule"])}
                                            slider_max={parseInt(config[popupContent.instance]["max_rule"])}
                                            slider_step={1}
                                            button_step={1}
                                            display_type={"int"}
                                            onButtonClick={onButtonClick}
                                            onSliderMove={onSliderMove}
                                        />

                                        {/* Fade duration input */}
                                        <div className={popupContent.fade_rule ? "text-center" : "d-none"}>
                                            <Form.Label className="mt-2">Duration (seconds)</Form.Label>
                                            <Form.Control
                                                type="text"
                                                value={popupContent.duration}
                                                onChange={(e) => set_popup_param("duration", e.target.value)}
                                            />
                                        </div>

                                        {/* Fade mode */}
                                        <div className="d-flex mt-2">
                                            <Form.Check
                                                id="fade-switch"
                                                type="switch"
                                                label="Fade"
                                                checked={popupContent.fade_rule}
                                                onChange={(e) => set_popup_param("fade_rule", e.target.checked)}
                                            />
                                        </div>
                                    </>
                                );
                            case "api_target":
                                return (
                                    <>
                                        <Button
                                            variant="secondary"
                                            onClick={() => handleShow(popupContent.instance, popupContent.timestamp)}
                                        >
                                            Set Rule
                                        </Button>
                                    </>
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
