import React, { useContext } from 'react';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';

function IPInput({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    return (
        <InputWrapper label="IP">
            <input
                type="text"
                className="form-control ip-input validate"
                placeholder=""
                value={instance.ip}
                pattern="^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
                onChange={(e) => handleInputChange(id, "ip", e.target.value)}
                required
            />
        </InputWrapper>
    );
}

export default IPInput;
