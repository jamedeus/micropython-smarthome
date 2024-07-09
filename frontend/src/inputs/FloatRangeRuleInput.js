import React from 'react';
import PropTypes from 'prop-types';
import RuleSlider from 'inputs/RuleSlider';

const FloatRangeRuleInput = ({ rule, setRule, min, max, sliderStep=0.5, onBlur=() => {} }) => {
    return (
        <RuleSlider
            rule={rule}
            setRule={setRule}
            min={min}
            max={max}
            sliderStep={sliderStep}
            buttonStep={0.5}
            displayType={"float"}
            onBlur={onBlur}
        />
    );
};

FloatRangeRuleInput.propTypes = {
    rule: PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string
    ]).isRequired,
    setRule: PropTypes.func.isRequired,
    min: PropTypes.number.isRequired,
    max: PropTypes.number.isRequired,
    sliderStep: PropTypes.number,
    onBlur: PropTypes.func
};

export default FloatRangeRuleInput;
