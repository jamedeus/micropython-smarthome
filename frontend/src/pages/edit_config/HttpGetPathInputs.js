import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import { EditConfigContext } from 'root/EditConfigContext';
import InputWrapper from 'inputs/InputWrapper';

const HttpGetPathInputs = ({ id }) => {
    // Get current state + callback functions from context
    const {
        config,
        handleInputChange,
        highlightInvalid
    } = useContext(EditConfigContext);

    // Get instance section in config
    const instance = config[id];

    return (
        <>
            <InputWrapper label="On path">
                <Form.Control
                    type="text"
                    placeholder="Appended to URI for on action"
                    value={instance.on_path}
                    onChange={(e) => handleInputChange(id, "on_path", e.target.value)}
                    isInvalid={(highlightInvalid && !instance.on_path)}
                />
            </InputWrapper>

            <InputWrapper label="Off path">
                <Form.Control
                    type="text"
                    placeholder="Appended to URI for off action"
                    value={instance.off_path}
                    onChange={(e) => handleInputChange(id, "off_path", e.target.value)}
                    isInvalid={(highlightInvalid && !instance.off_path)}
                />
            </InputWrapper>
        </>
    );
};

HttpGetPathInputs.propTypes = {
    id: PropTypes.string.isRequired
};

export default HttpGetPathInputs;
