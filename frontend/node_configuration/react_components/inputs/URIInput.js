import React, { useContext, useRef, useEffect } from 'react';
import Form from 'react-bootstrap/Form';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';

function URIInput({ key, id }) {
    const input = useRef(null);

    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    // Validate when focus leaves, add highlight if invalid
    useEffect(() => {
        input.current.addEventListener("blur", () => {
            if (!input.current.validity.valid) {
                input.current.classList.add('is-invalid');
            };
        });
    }, []);

    // Remove invalid highlight immediately when contents become valid
    const validate = (event) => {
        if (event.target.validity.valid) {
            event.target.classList.remove('is-invalid');
        }
        handleInputChange(id, "uri", event.target.value);
    }

    return (
        <InputWrapper label="URI">
            <Form.Control
                ref={input}
                type="text"
                placeholder="IP address or URL"
                value={instance.uri}
                pattern="(?:(?:http|https):\/\/)?(?:\S+(?::\S*)?@)?(?:(?:[0-9]{1,3}\.){3}[0-9]{1,3})(?::\d{1,5})?|(?:(?:http|https):\/\/)?[a-zA-Z0-9.]+(?:-[a-zA-Z0-9]+)*(?:\.[a-zA-Z]{2,6})+(?:\/\S*)?"
                onChange={(e) => validate(e)}
            />
        </InputWrapper>
    );
}

export default URIInput;
