import React from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import { Range, getTrackBackground } from 'react-range';
import { scaleToRange } from 'util/helper_functions';

// Slider range set with min and max args
// Slider will scale current rule to 1-100 unless a custom range is defined
// with displayMin and/or displayMax, or if scaleDisplayValue is false
const RuleSlider = ({
    rule,
    setRule,
    min,
    max,
    displayMin=1,
    displayMax=100,
    scaleDisplayValue=true,
    sliderStep,
    buttonStep,
    displayType,
    onBlur=() => {}
}) => {
    // Prevent slider leaving track if upstream rule exceeds limits.
    // Some inputs (eg motion sensor) have limits on frontend but not firmware.
    // If rule is set outside frontend range using CLI client this will prevent
    // page from loading (or move slider outside track if page already loaded).
    if (parseFloat(rule) > max) {
        rule = max;
    } else if (parseFloat(rule) < min) {
        rule = min;
    }

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
            new_rule = parseFloat(min);
        } else if (new_rule > parseFloat(max)) {
            new_rule = parseFloat(max);
        }

        // Pass new rule to callback, call onBlur to prevent getting stuck in
        // edit mode (blocks status updates on ApiCard page)
        setRule(new_rule);
        onBlur();
    };

    // Returns rule scaled to the range displayMin - displayMax
    // Ex: Returns 70 if rule=700, min=1, max=1000, displayMin=1, displayMax=100
    const getScaledRule = () => {
        return scaleToRange(rule, min, max, displayMin, displayMax);
    };

    // Returns value displayed on slider handle
    // Scales value to display range unless scaleDisplayValue is false
    const getThumbValue = () => {
        const displayValue = scaleDisplayValue ? getScaledRule() : rule;

        switch(displayType) {
            case("int"):
                return parseInt(displayValue);
            case("float"):
                return parseFloat(displayValue).toFixed(1);
            default:
                /* istanbul ignore next */
                return displayValue;
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

            <div className="w-100 mx-4">
                <Range
                    step={sliderStep}
                    min={min}
                    max={max}
                    values={values}
                    onChange={
                        /* istanbul ignore next */
                        (values) => setRule(values[0])
                    }
                    onFinalChange={onBlur}
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
    ]).isRequired,
    setRule: PropTypes.func.isRequired,
    min: PropTypes.number.isRequired,
    max: PropTypes.number.isRequired,
    displayMin: PropTypes.number,
    displayMax: PropTypes.number,
    scaleDisplayValue: PropTypes.bool,
    sliderStep: PropTypes.number.isRequired,
    buttonStep: PropTypes.number.isRequired,
    displayType: PropTypes.string.isRequired,
    style: PropTypes.object,
    onBlur: PropTypes.func
};

export default RuleSlider;
