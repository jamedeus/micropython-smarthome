import React from 'react';
import PropTypes from 'prop-types';
import RuleSlider from 'inputs/RuleSlider';

const IntRangeRuleInput = ({ rule, setRule, min, max }) => {
    // Handler for slider + and - buttons
    const handleButtonClick = (rule, direction, min, max) => {
        let new_rule;
        if (direction === "up") {
            new_rule = parseInt(rule) + 1;
        } else {
            new_rule = parseInt(rule) - 1;
        }

        // Enforce rule limits
        if (new_rule < parseInt(min)) {
            new_rule = parseInt(max);
        } else if (new_rule > parseInt(max)) {
            new_rule = parseInt(max);
        }

        setRule(new_rule);
    };

    return (
        <RuleSlider
            rule_value={rule}
            slider_min={min}
            slider_max={max}
            slider_step={1}
            button_step={1}
            display_type={"int"}
            onButtonClick={handleButtonClick}
            onSliderMove={setRule}
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
