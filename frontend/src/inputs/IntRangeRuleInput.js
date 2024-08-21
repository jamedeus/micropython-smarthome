import React from 'react';
import PropTypes from 'prop-types';
import RuleSlider from 'inputs/RuleSlider';

const IntRangeRuleInput = ({
    rule,
    setRule,
    min,
    max,
    displayMin=1,
    displayMax=100,
    scaleDisplayValue=true,
    onBlur=() => {}
}) => {
    // Calculate 1% of range
    const buttonStep = Math.round((max - min) / 100);

    return (
        <RuleSlider
            rule={rule}
            setRule={setRule}
            min={min}
            max={max}
            displayMin={displayMin}
            displayMax={displayMax}
            scaleDisplayValue={scaleDisplayValue}
            sliderStep={1}
            buttonStep={buttonStep}
            displayType={"int"}
            onBlur={onBlur}
        />
    );
};

IntRangeRuleInput.propTypes = {
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
    onBlur: PropTypes.func
};

export default IntRangeRuleInput;
