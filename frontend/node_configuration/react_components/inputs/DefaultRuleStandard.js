import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from './../ConfigContext';
import Dropdown from './Dropdown';

function DefaultRuleStandard({ id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    const onChange = (value) => {
        handleInputChange(id, "default_rule", value);
    };

    return (
        <Dropdown
            value={instance.default_rule}
            options={["Enabled", "Disabled"]}
            onChange={onChange}
            label="Default Rule"
        />
    );
}

DefaultRuleStandard.propTypes = {
    id: PropTypes.string,
}

export default DefaultRuleStandard;
