import React from 'react';
import PropTypes from 'prop-types';
import RuleSlider from 'inputs/RuleSlider';

const IntRangeRuleInput = ({ rule, setRule, min, max }) => {
    return (
        <RuleSlider
            rule={rule}
            setRule={setRule}
            min={min}
            max={max}
            sliderStep={1}
            buttonStep={1}
            displayType={"int"}
        />
    );
};

IntRangeRuleInput.propTypes = {
    rule: PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string
    ]),
    setRule: PropTypes.func,
    min: PropTypes.number,
    max: PropTypes.number
};

export default IntRangeRuleInput;
