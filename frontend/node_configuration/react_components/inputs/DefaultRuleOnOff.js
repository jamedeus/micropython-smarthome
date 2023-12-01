import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from './../ConfigContext';
import Dropdown from './Dropdown';

function DefaultRuleOnOff({ id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange, highlightInvalid } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    const onChange = (value) => {
        handleInputChange(id, "default_rule", value);
    };

    return (
        <Dropdown
            value={instance.default_rule}
            options={["On", "Off"]}
            onChange={onChange}
            label="Default Rule"
            isInvalid={(highlightInvalid && !instance.default_rule)}
        />
    );
}

DefaultRuleOnOff.propTypes = {
    id: PropTypes.string,
};

export default DefaultRuleOnOff;
