import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';

function HttpGetPathInputs({ id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

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
                />
            </InputWrapper>

            <InputWrapper label="Off path">
                <Form.Control
                    type="text"
                    placeholder="Appended to URI for off action"
                    value={instance.off_path}
                    onChange={(e) => handleInputChange(id, "off_path", e.target.value)}
                />
            </InputWrapper>
        </>
    );
}

HttpGetPathInputs.propTypes = {
    id: PropTypes.string
}

export default HttpGetPathInputs;
