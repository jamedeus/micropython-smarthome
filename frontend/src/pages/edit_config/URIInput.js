import React, { useContext, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import { EditConfigContext } from 'root/EditConfigContext';
import InputWrapper from 'inputs/InputWrapper';

const URIInput = ({ id }) => {
    const input = useRef(null);

    // Get current state + callback functions from context
    const {
        config,
        handleInputChange,
        highlightInvalid
    } = useContext(EditConfigContext);

    // Get instance section in config
    const instance = config[id];

    // Validate when focus leaves, add highlight if invalid
    useEffect(() => {
        input.current.addEventListener("blur", () => {
            if (!input.current.validity.valid) {
                input.current.classList.add('is-invalid');
            }
        });
    }, []);

    // Remove invalid highlight immediately when contents become valid
    const validate = (event) => {
        if (event.target.validity.valid) {
            event.target.classList.remove('is-invalid');
        }
        handleInputChange(id, "uri", event.target.value);
    };

    return (
        <InputWrapper label="URI">
            <Form.Control
                ref={input}
                type="text"
                placeholder="IP address or URL"
                value={instance.uri}
                pattern="(?:(?:http|https):\/\/)?(?:\S+(?::\S*)?@)?(?:(?:[0-9]{1,3}\.){3}[0-9]{1,3})(?::\d{1,5})?|(?:(?:http|https):\/\/)?[a-zA-Z0-9.]+(?:-[a-zA-Z0-9]+)*(?:\.[a-zA-Z]{2,6})+(?:\/\S*)?"
                onChange={(e) => validate(e)}
                isInvalid={(highlightInvalid && !instance.uri)}
            />
        </InputWrapper>
    );
};

URIInput.propTypes = {
    id: PropTypes.string.isRequired
};

export default URIInput;
