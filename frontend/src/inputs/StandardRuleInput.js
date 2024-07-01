import React from 'react';
import PropTypes from 'prop-types';
import Dropdown from './Dropdown';

const StandardRuleInput = ({ rule, setRule, label="", isInvalid=false }) => {
    return (
        <Dropdown
            value={rule}
            options={["Enabled", "Disabled"]}
            onChange={(value) => setRule(value)}
            label={label}
            isInvalid={isInvalid}
        />
    );
};

StandardRuleInput.propTypes = {
    rule: PropTypes.string,
    setRule: PropTypes.func,
    label: PropTypes.string,
    isInvalid: PropTypes.bool
};

export default StandardRuleInput;
