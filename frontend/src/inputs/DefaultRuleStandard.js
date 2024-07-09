import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from 'root/ConfigContext';
import StandardRuleInput from 'inputs/StandardRuleInput';

const DefaultRuleStandard = ({ id }) => {
    // Get curent state + callback functions from context
    const { config, handleInputChange, highlightInvalid } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    const onChange = (value) => {
        handleInputChange(id, "default_rule", value);
    };

    return (
        <StandardRuleInput
            rule={instance.default_rule}
            setRule={onChange}
            label="Default Rule"
            isInvalid={(highlightInvalid && !instance.default_rule)}
        />
    );
};

DefaultRuleStandard.propTypes = {
    id: PropTypes.string.isRequired
};

export default DefaultRuleStandard;
