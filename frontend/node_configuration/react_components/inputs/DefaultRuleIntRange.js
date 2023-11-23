import React, { useContext, useState } from 'react';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import { Range, getTrackBackground } from 'react-range';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';
import { get_instance_metadata } from './../metadata';


// Takes 2 numbers (int, float, or string) and returns average
function average(a, b) {
    try {
        return parseInt((parseFloat(a) + parseFloat(b)) / 2);
    } catch(err) {
        console.log(err);
    };
};


function DefaultRuleIntRange({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange, handleInstanceUpdate, handleSliderButton } = useContext(ConfigContext);

    // Get instance section from config (state) object
    const instance = config[id];

    // Get metadata object for selected type (contains slider min/max)
    const category = id.replace(/[0-9]/g, '');
    const instanceMetadata = get_instance_metadata(category, instance._type);

    // Replace empty params with defaults (slider component requires all)
    if (!instance.min_rule) {
        instance.min_rule = instanceMetadata.rule_limits[0];
    };
    if (!instance.max_rule) {
        instance.max_rule = instanceMetadata.rule_limits[1];
    };
    if (!instance.default_rule) {
        instance.default_rule = average(instance.min_rule, instance.max_rule);
    };

    // Create array containing current rule, required my slider component
    const values = [instance.default_rule]

    // Handler for rule limit inputs
    const setRuleLimits = (param, value) => {
        // Remove non-numeric characters, cast to int
        value = parseInt(value.replace(/[^0-9.]/g, ''));
        // Default to 1 when input is completely empty
        if (isNaN(value)) {
            value = 1;
        }

        // Enforce absolute rule limits
        const metadata_min = parseInt(instanceMetadata.rule_limits[0], 10);
        const metadata_max = parseInt(instanceMetadata.rule_limits[1], 10);
        value = Math.max(metadata_min, Math.min(value, metadata_max));

        // Copy state object, add new limit
        const update = { ...instance, [param]: value };

        // Prevent max lower than min, min higher than max, default_rule out of range
        if (param === "min_rule") {
            update.max_rule = Math.max(update.max_rule, value);
            update.default_rule = Math.max(update.default_rule, value);
        } else if (param === "max_rule") {
            update.min_rule = Math.min(update.min_rule, value);
            update.default_rule = Math.min(update.default_rule, value);
        }

        handleInstanceUpdate(id, update);
    };


    // Set default state for advanced settings collapse
    const [open, setOpen] = useState(false);

    return (
        <>
            <InputWrapper label="Default Rule">
                <div className="d-flex flex-row align-items-center my-2">
                    <Button
                        variant="none"
                        size="sm"
                        onClick={(e) => handleSliderButton(id, 1, "down")}
                    >
                        <i className="bi-dash-lg"></i>
                    </Button>

                    <div className="w-100 mx-3">
                        <Range
                            step={1}
                            min={parseInt(instance.min_rule)}
                            max={parseInt(instance.max_rule)}
                            values={values}
                            onChange={(values) => handleInputChange(id, "default_rule", values[0])}
                            renderTrack={({ props, children }) => (
                                <div
                                    {...props}
                                    style={{
                                        ...props.style,
                                        height: '8px',
                                        width: '100%',
                                        borderRadius: '4px',
                                        background: getTrackBackground({
                                            values,
                                            colors: ['#0D6EFD', '#1B1E1F'],
                                            min: instance.min_rule,
                                            max: instance.max_rule
                                        }),
                                    }}
                                >
                                    {children}
                                </div>
                            )}
                            renderThumb={({ props }) => (
                                <div
                                    {...props}
                                    style={{
                                        ...props.style,
                                        height: '42px',
                                        width: '42px',
                                        borderRadius: '100%',
                                        backgroundColor: '#0D6EFD',
                                        display: 'flex',
                                        justifyContent: 'center',
                                        alignItems: 'center',
                                        fontWeight: 'bold',
                                        outline: 'none',
                                    }}
                                >
                                    {parseInt(values[0])}
                                </div>
                            )}
                        />
                    </div>

                    <Button
                        variant="none"
                        size="sm"
                        onClick={(e) => handleSliderButton(id, 1, "up")}
                    >
                        <i className="bi-plus-lg"></i>
                    </Button>
                </div>
            </InputWrapper>

            <div className="mt-3 text-center">
                <a className="text-decoration-none text-dim" role="button" onClick={() => setOpen(!open)}>
                    Advanced
                </a>
            </div>

            <Collapse in={open}>
                <div>
                    <InputWrapper label="Min brightness">
                        <Form.Control
                            type="text"
                            value={instance.min_rule}
                            onChange={(e) => setRuleLimits("min_rule", e.target.value)}
                        />
                    </InputWrapper>

                    <InputWrapper label="Max brightness">
                        <Form.Control
                            type="text"
                            value={instance.max_rule}
                            onChange={(e) => setRuleLimits("max_rule", e.target.value)}
                        />
                    </InputWrapper>
                </div>
            </Collapse>
        </>
    );
}

export default DefaultRuleIntRange;
