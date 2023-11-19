import React, { useContext } from 'react';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';

function HttpGetPathInputs({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    return (
        <>
            <InputWrapper label="On path">
                <input
                    type="text"
                    className="form-control validate"
                    placeholder="Appended to URI for on action"
                    value={instance.on_path}
                    onChange={(e) => handleInputChange(id, "on_path", e.target.value)}
                    required
                />
            </InputWrapper>

            <InputWrapper label="Off path">
                <input
                    type="text"
                    className="form-control validate"
                    placeholder="Appended to URI for off action"
                    value={instance.off_path}
                    onChange={(e) => handleInputChange(id, "off_path", e.target.value)}
                    required
                />
            </InputWrapper>
        </>
    );
}

export default HttpGetPathInputs;
