import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from 'root/ConfigContext';
import OnOffRuleInput from 'inputs/OnOffRuleInput';

const DefaultRuleOnOff = ({ id, instance }) => {
    const { handleInputChange, highlightInvalid } = useContext(ConfigContext);

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
    id: PropTypes.string.isRequired,
    instance: PropTypes.object.isRequired
};

export default DefaultRuleOnOff;
