import React, { useContext } from 'react';
import Form from 'react-bootstrap/Form';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';


function NicknameInput({ id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    // Check for duplicate nickname, set bool that controls invalid highlight
    let duplicate = false;
    for (const[key, value] of Object.entries(config) ) {
        // If not same instance, has nickname param, and nickname is not blank
        if (key !== id && value.nickname !== undefined && instance.nickname) {
            if (value.nickname.toLowerCase() === instance.nickname.toLowerCase()) {
                duplicate = true;
                break;
            }
        }
    }

    return (
        <InputWrapper label="Nickname">
            <Form.Control
                type="text"
                value={instance.nickname}
                onChange={(e) => handleInputChange(id, "nickname", e.target.value)}
                isInvalid={duplicate}
            />
        </InputWrapper>
    );
}

export default NicknameInput;
