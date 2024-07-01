import React from 'react';
import PropTypes from 'prop-types';
import RuleSlider from 'inputs/RuleSlider';

const FloatRangeRuleInput = ({ rule, setRule, min, max, sliderStep=0.5 }) => {
    // Handler for slider + and - buttons
    const handleButtonClick = (rule, direction, min, max) => {
        let new_rule;
        if (direction === "up") {
            new_rule = parseFloat(rule) + 0.5;
        } else {
            new_rule = parseFloat(rule) - 0.5;
        }

        // Enforce rule limits
        if (new_rule < parseFloat(min)) {
            new_rule = parseFloat(max);
        } else if (new_rule > parseFloat(max)) {
            new_rule = parseFloat(max);
        }

        setRule(new_rule);
    };

    return (
        <RuleSlider
            rule_value={rule}
            slider_min={min}
            slider_max={max}
            slider_step={sliderStep}
            button_step={0.5}
            display_type={"float"}
            onButtonClick={handleButtonClick}
            onSliderMove={setRule}
        />
    );
};

FloatRangeRuleInput.propTypes = {
    rule: PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string
    ]),
    setRule: PropTypes.func,
    min: PropTypes.number,
    max: PropTypes.number,
    sliderStep: PropTypes.number
};

export default FloatRangeRuleInput;
