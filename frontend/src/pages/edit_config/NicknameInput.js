import React, { useContext, useEffect } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import { ConfigContext } from 'root/ConfigContext';
import InputWrapper from 'inputs/InputWrapper';

const NicknameInput = ({ id }) => {
    // Get curent state + callback functions from context
    const {
        config,
        handleInputChange,
        highlightInvalid,
        setHasInvalidFields,
    } = useContext(ConfigContext);

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

    // Disable next page button until duplicate nickname fixed
    useEffect(() => {
        setHasInvalidFields(duplicate);
    }, [duplicate]);

    // Add invalid highlight if nickname is duplicate OR nickname is still
    // blank after page validation runs
    let invalid = false;
    if (duplicate || highlightInvalid && !instance.nickname) {
        invalid = true;
    }

    return (
        <InputWrapper label="Nickname">
            <Form.Control
                type="text"
                value={instance.nickname}
                onChange={(e) => handleInputChange(id, "nickname", e.target.value)}
                isInvalid={invalid}
            />
        </InputWrapper>
    );
};

NicknameInput.propTypes = {
    id: PropTypes.string.isRequired
};

export default NicknameInput;
