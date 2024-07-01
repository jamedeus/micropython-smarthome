import React from 'react';
import PropTypes from 'prop-types';
import RuleSlider from 'inputs/RuleSlider';

const FloatRangeRuleInput = ({ rule, setRule, min, max, sliderStep=0.5 }) => {
    return (
        <RuleSlider
            rule={rule}
            setRule={setRule}
            min={min}
            max={max}
            sliderStep={sliderStep}
            buttonStep={0.5}
            displayType={"float"}
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
