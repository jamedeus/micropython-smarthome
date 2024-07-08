import React from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import { Range, getTrackBackground } from 'react-range';

const RuleSlider = ({ rule, setRule, min, max, sliderStep, buttonStep, displayType }) => {
    // Create array containing current rule, required my slider component
    const values = [rule];

    // Handler for slider + and - buttons
    const handleButtonClick = (rule, direction) => {
        let new_rule;
        if (direction === "up") {
            new_rule = parseFloat(rule) + parseFloat(buttonStep);
        } else {
            new_rule = parseFloat(rule) - parseFloat(buttonStep);
        }

        // Enforce rule limits
        if (new_rule < parseFloat(min)) {
            new_rule = parseFloat(max);
        } else if (new_rule > parseFloat(max)) {
            new_rule = parseFloat(max);
        }

        setRule(new_rule);
    };

    // Returns value displayed on slider handle
    const getThumbValue = () => {
        switch(displayType) {
            case("int"):
                return parseInt(rule);
            case("float"):
                return parseFloat(rule).toFixed(1);
            default:
                return rule;
        }
    };

    // Return slider with values set from args
    return (
        <div className="d-flex flex-row align-items-center my-2">
            <Button
                variant="none"
                size="sm"
                onClick={() => handleButtonClick(rule, "down")}
            >
                <i className="bi-dash-lg"></i>
            </Button>

            <div className="w-100 mx-3">
                <Range
                    step={sliderStep}
                    min={min}
                    max={max}
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
                                    min: min,
                                    max: max
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
                onClick={() => handleButtonClick(rule, "up")}
            >
                <i className="bi-plus-lg"></i>
            </Button>
        </div>
    );
};

RuleSlider.propTypes = {
    rule: PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string
    ]),
    setRule: PropTypes.func,
    min: PropTypes.number,
    max: PropTypes.number,
    sliderStep: PropTypes.number,
    buttonStep: PropTypes.number,
    displayType: PropTypes.string,
    onButtonClick: PropTypes.func,
    style: PropTypes.object
};

export default RuleSlider;
