import React from 'react';
import PropTypes from 'prop-types';
import RuleSlider from 'inputs/RuleSlider';

const IntRangeRuleInput = ({ rule, setRule, min, max }) => {
    return (
        <RuleSlider
            rule_value={rule}
            slider_min={min}
            slider_max={max}
            slider_step={1}
            button_step={1}
            display_type={"int"}
            setRule={setRule}
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
