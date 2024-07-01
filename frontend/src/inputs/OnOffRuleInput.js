import React from 'react';
import PropTypes from 'prop-types';
import Dropdown from './Dropdown';

const OnOffRuleInput = ({ rule, setRule, label="", isInvalid=false, includeStandardRules=true }) => {
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
        />
    );
};

OnOffRuleInput.propTypes = {
    rule: PropTypes.string,
    setRule: PropTypes.func,
    label: PropTypes.string,
    isInvalid: PropTypes.bool,
    includeStandardRules: PropTypes.bool
};

export default OnOffRuleInput;
