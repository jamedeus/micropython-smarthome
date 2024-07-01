import React from 'react';
import PropTypes from 'prop-types';
import RuleSlider from 'inputs/RuleSlider';

const FloatRangeRuleInput = ({ rule, setRule, min, max, sliderStep=0.5 }) => {
    return (
        <RuleSlider
            rule_value={rule}
            slider_min={min}
            slider_max={max}
            slider_step={sliderStep}
            button_step={0.5}
            display_type={"float"}
            setRule={setRule}
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
