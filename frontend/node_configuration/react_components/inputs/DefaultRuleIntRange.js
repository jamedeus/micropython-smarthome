import React, { useContext } from 'react';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import { Range, getTrackBackground } from 'react-range';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';

function DefaultRuleIntRange({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange, handleSliderButton } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    // TODO find a better way
    const category = id.replace(/[0-9]/g, '');
    const instanceMetadata = metadata[`${category}s`][instance._type];

    // Create array containing current rule, required my slider component
    const values = [instance.default_rule]

    // Handler for rule limit inputs
    const setRuleLimits = (param, value) => {
        // Remove non-numeric characters
        value = value.replace(/[^0-9.]/g, '');

        // Enforce rule limits
        if (parseInt(value) < instanceMetadata.rule_limits[0]) {
            value = instanceMetadata.rule_limits[0];
        } else if (parseInt(value) > instanceMetadata.rule_limits[1]) {
            value = instanceMetadata.rule_limits[1];
        };

        // Prevent max lower than min, min higher than max
        if (param === "min_rule" && parseInt(value) > parseInt(instance.max_rule)) {
            console.log("min can't be higher than max")
            value = instance.max_rule;
        } else if (param === "max_rule" && parseInt(value) < parseInt(instance.min_rule)) {
            console.log("max can't be lower than min")
            value = instance.min_rule;
        }
        handleInputChange(id, param, value);
    };

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
                            min={instance.min_rule}
                            max={instance.max_rule}
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
                <a className="text-decoration-none text-dim" data-bs-toggle="collapse" href={`#${id}-advanced_settings`} role="button" aria-expanded="false" aria-controls={`${id}-advanced_settings`}>Advanced</a>
            </div>

            <div id={`${id}-advanced_settings`} className="collapse">
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
        </>
    );
}

export default DefaultRuleIntRange;
