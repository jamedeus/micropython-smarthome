import React, { useContext } from 'react';
import Button from 'react-bootstrap/Button';
import { Range, getTrackBackground } from 'react-range';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';

function DefaultRuleFloatRange({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange, handleSliderButton } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    // TODO find a better way
    const category = id.replace(/[0-9]/g, '');
    const instanceMetadata = metadata[`${category}s`][instance._type];

    // Create array containing current rule, required my slider component
    const values = [instance.default_rule];

    return (
        <InputWrapper label="Default Rule">
            <div className="d-flex flex-row align-items-center my-2">
                <Button
                    variant="none"
                    size="sm"
                    onClick={(e) => handleSliderButton(id, 0.5, "down")}
                >
                    <i className="bi-dash-lg"></i>
                </Button>

                <div className="w-100 mx-3">
                    <Range
                        step={0.5}
                        min={instanceMetadata.rule_limits[0]}
                        max={instanceMetadata.rule_limits[1]}
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
                                        min: instanceMetadata.rule_limits[0],
                                        max: instanceMetadata.rule_limits[1]
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
                                {parseFloat(values[0]).toFixed(1)}
                            </div>
                        )}
                    />
                </div>

                <Button
                    variant="none"
                    size="sm"
                    onClick={(e) => handleSliderButton(id, 0.5, "up")}
                >
                    <i className="bi-plus-lg"></i>
                </Button>
            </div>
        </InputWrapper>
    );
}

export default DefaultRuleFloatRange;
