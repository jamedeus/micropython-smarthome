import React, { useContext } from 'react';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';

function URIInput({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    return (
        <InputWrapper label="URI">
            <input
                type="text"
                className="form-control validate"
                placeholder="IP address or URL"
                value={instance.uri}
                pattern="(?:(?:http|https):\/\/)?(?:\S+(?::\S*)?@)?(?:(?:[0-9]{1,3}\.){3}[0-9]{1,3})(?::\d{1,5})?|(?:(?:http|https):\/\/)?[a-zA-Z0-9.]+(?:-[a-zA-Z0-9]+)*(?:\.[a-zA-Z]{2,6})+(?:\/\S*)?"
                onChange={(e) => handleInputChange(id, "uri", e.target.value)}
                required
            />
        </InputWrapper>
    );
}

export default URIInput;
