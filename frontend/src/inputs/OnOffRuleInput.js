import React from 'react';
import PropTypes from 'prop-types';
import Dropdown from './Dropdown';

const OnOffRuleInput = ({ rule, setRule, label="", isInvalid=false, includeStandardRules=true, focus=false }) => {
    return (
        <Dropdown
            value={rule}
            options={includeStandardRules
                ? ["Enabled", "Disabled", "On", "Off"]
                : ["On", "Off"]
            }
            onChange={(value) => setRule(value)}
            label={label}
            isInvalid={isInvalid}
            focus={focus}
        />
    );
};

OnOffRuleInput.propTypes = {
    rule: PropTypes.string.isRequired,
    setRule: PropTypes.func.isRequired,
    label: PropTypes.string,
    isInvalid: PropTypes.bool,
    includeStandardRules: PropTypes.bool,
    focus: PropTypes.bool
};

export default OnOffRuleInput;
