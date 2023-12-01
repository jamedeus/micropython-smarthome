import React from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import { Range, getTrackBackground } from 'react-range';

function RuleSlider({ rule_value, slider_min, slider_max, slider_step, button_step, display_type, onButtonClick, onSliderMove }) {
    // Create array containing current rule, required my slider component
    const values = [rule_value];

    // Return slider with values set from args
    return (
        <div className="d-flex flex-row align-items-center my-2">
            <Button
                variant="none"
                size="sm"
                onClick={() => onButtonClick(button_step, "down", slider_min, slider_max)}
            >
                <i className="bi-dash-lg"></i>
            </Button>

            <div className="w-100 mx-3">
                <Range
                    step={slider_step}
                    min={slider_min}
                    max={slider_max}
                    values={values}
                    onChange={(values) => onSliderMove(values[0])}
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
                                    min: slider_min,
                                    max: slider_max
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
                            {(() => {
                                if (display_type === "int") {
                                    return parseInt(values[0]);
                                } else if (display_type === "float") {
                                    return parseFloat(values[0]).toFixed(1);
                                } else {
                                    return values[0];
                                }
                            })()}
                        </div>
                    )}
                />
            </div>

            <Button
                variant="none"
                size="sm"
                onClick={() => onButtonClick(button_step, "up", slider_min, slider_max)}
            >
                <i className="bi-plus-lg"></i>
            </Button>
        </div>
    );
}

RuleSlider.propTypes = {
    rule_value: PropTypes.string,
    slider_min: PropTypes.number,
    slider_max: PropTypes.number,
    slider_step: PropTypes.number,
    button_step: PropTypes.number,
    display_type: PropTypes.string,
    onButtonClick: PropTypes.func,
    onSliderMove: PropTypes.func,
    style: PropTypes.object
};

export default RuleSlider;
