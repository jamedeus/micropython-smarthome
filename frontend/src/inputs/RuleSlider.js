import React from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import { Range, getTrackBackground } from 'react-range';

function RuleSlider({ rule_value, slider_min, slider_max, slider_step, button_step, display_type, setRule }) {
    // Create array containing current rule, required my slider component
    const values = [rule_value];

    // Handler for slider + and - buttons
    const handleButtonClick = (rule, direction) => {
        let new_rule;
        if (direction === "up") {
            new_rule = parseFloat(rule) + parseFloat(button_step);
        } else {
            new_rule = parseFloat(rule) - parseFloat(button_step);
        }

        // Enforce rule limits
        if (new_rule < parseFloat(slider_min)) {
            new_rule = parseFloat(slider_max);
        } else if (new_rule > parseFloat(slider_max)) {
            new_rule = parseFloat(slider_max);
        }

        setRule(new_rule);
    };

    // Returns value displayed on slider handle
    const getThumbValue = () => {
        switch(display_type) {
            case("int"):
                return parseInt(values[0]);
            case("float"):
                return parseFloat(values[0]).toFixed(1);
            default:
                return values[0];
        }
    };

    // Return slider with values set from args
    return (
        <div className="d-flex flex-row align-items-center my-2">
            <Button
                variant="none"
                size="sm"
                onClick={() => handleButtonClick(values[0], "down")}
            >
                <i className="bi-dash-lg"></i>
            </Button>

            <div className="w-100 mx-3">
                <Range
                    step={slider_step}
                    min={slider_min}
                    max={slider_max}
                    values={values}
                    onChange={(values) => setRule(values[0])}
                    renderTrack={({ props, children }) => (
                        <div
                            {...props}
                            className="sliderTrack"
                            style={{
                                ...props.style,
                                background: getTrackBackground({
                                    values,
                                    colors: [
                                        'var(--slider-track-fill)',
                                        'var(--slider-track-background)'
                                    ],
                                    min: slider_min,
                                    max: slider_max
                                }),
                            }}
                        >
                            {children}
                        </div>
                    )}
                    renderThumb={({ props }) => (
                        <div {...props} className="sliderHandle">
                            {getThumbValue()}
                        </div>
                    )}
                />
            </div>

            <Button
                variant="none"
                size="sm"
                onClick={() => handleButtonClick(values[0], "up")}
            >
                <i className="bi-plus-lg"></i>
            </Button>
        </div>
    );
}

RuleSlider.propTypes = {
    rule_value: PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string
    ]),
    slider_min: PropTypes.number,
    slider_max: PropTypes.number,
    slider_step: PropTypes.number,
    button_step: PropTypes.number,
    display_type: PropTypes.string,
    onButtonClick: PropTypes.func,
    setRule: PropTypes.func,
    style: PropTypes.object
};

export default RuleSlider;
