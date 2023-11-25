import React, { useContext } from 'react';
import { ConfigContext } from './../ConfigContext';
import Dropdown from './Dropdown';


function DefaultRuleOnOff({ key, id }) {
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
            options={["On", "Off"]}
            onChange={onChange}
            label="Default Rule"
        />
    );
}


export default DefaultRuleOnOff;
