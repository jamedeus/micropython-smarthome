import React, { useContext } from 'react';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';

function NicknameInput({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    return (
        <InputWrapper label="Nickname">
            <input
                type="text"
                className="form-control nickname"
                placeholder=""
                value={instance.nickname}
                onChange={(e) => handleInputChange(id, "nickname", e.target.value)}
                required
            />
        </InputWrapper>
    );
}

export default NicknameInput;
