import React from 'react';
import PropTypes from 'prop-types';
import RuleSlider from 'inputs/RuleSlider';

const FloatRangeRuleInput = ({
    rule,
    setRule,
    min,
    max,
    displayMin=1,
    displayMax=100,
    scaleDisplayValue=false,
    sliderStep=0.5,
    onBlur=() => {}
}) => {
    return (
        <RuleSlider
            rule={rule}
            setRule={setRule}
            min={min}
            max={max}
            displayMin={displayMin}
            displayMax={displayMax}
            scaleDisplayValue={scaleDisplayValue}
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
    displayMin: PropTypes.number,
    displayMax: PropTypes.number,
    scaleDisplayValue: PropTypes.bool,
    sliderStep: PropTypes.number,
    onBlur: PropTypes.func
};

export default FloatRangeRuleInput;
