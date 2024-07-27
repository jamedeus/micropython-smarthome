import React from 'react';
import PropTypes from 'prop-types';
import Dropdown from './Dropdown';

const StandardRuleInput = ({ rule, setRule, label="", isInvalid=false, focus=false }) => {
    return (
        <Dropdown
            value={rule}
            options={["Enabled", "Disabled"]}
            onChange={(value) => setRule(value)}
            label={label}
            isInvalid={isInvalid}
            focus={focus}
        />
    );
};

StandardRuleInput.propTypes = {
    rule: PropTypes.string.isRequired,
    setRule: PropTypes.func.isRequired,
    label: PropTypes.string,
    isInvalid: PropTypes.bool,
    focus: PropTypes.bool
};

export default StandardRuleInput;
