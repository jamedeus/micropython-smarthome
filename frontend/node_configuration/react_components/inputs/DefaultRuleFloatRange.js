import React, { useContext } from 'react';
import Button from 'react-bootstrap/Button';
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


function DefaultRuleFloatRange({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange, handleSliderButton } = useContext(ConfigContext);

    // Get instance section from config (state) object
    const instance = config[id];

    // Get metadata object for selected type (contains slider min/max)
    const category = id.replace(/[0-9]/g, '');
    const instanceMetadata = get_instance_metadata(category, instance._type);
    const min_rule = parseInt(instanceMetadata.rule_limits[0], 10);
    const max_rule = parseInt(instanceMetadata.rule_limits[1], 10);

    // Replace empty default_rule when new card added (causes NaN on slider)
    if (!instance.default_rule) {
        instance.default_rule = average(min_rule, max_rule);
    };

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
                        min={min_rule}
                        max={max_rule}
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
                                        min: min_rule,
                                        max: max_rule
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
