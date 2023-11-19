import React, { useContext } from 'react';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';

function DefaultRuleOnOff({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    return (
        <InputWrapper label="Default Rule">
            <select className="form-select" value={instance.default_rule} autoComplete="off" onChange={(e) => handleInputChange(id, "default_rule", e.target.value)} required>
                <option disabled>Select default rule</option>
                <option value="on">On</option>
                <option value="off">Off</option>
            </select>
        </InputWrapper>
    );
}

export default DefaultRuleOnOff;
