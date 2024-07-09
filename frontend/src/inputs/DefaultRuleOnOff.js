import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from 'root/ConfigContext';
import OnOffRuleInput from 'inputs/OnOffRuleInput';

const DefaultRuleOnOff = ({ id }) => {
    // Get curent state + callback functions from context
    const { config, handleInputChange, highlightInvalid } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    const onChange = (value) => {
        handleInputChange(id, "default_rule", value);
    };

    return (
        <OnOffRuleInput
            rule={instance.default_rule}
            setRule={onChange}
            label="Default Rule"
            isInvalid={(highlightInvalid && !instance.default_rule)}
            includeStandardRules={false}
        />
    );
};

DefaultRuleOnOff.propTypes = {
    id: PropTypes.string.isRequired
};

export default DefaultRuleOnOff;
