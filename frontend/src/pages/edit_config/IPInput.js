import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import { EditConfigContext } from 'root/EditConfigContext';
import InputWrapper from 'inputs/InputWrapper';
import { formatIp } from 'util/validation';

const IPInput = ({ id }) => {
    // Get current state + callback functions from context
    const {
        config,
        handleInputChange,
        highlightInvalid
    } = useContext(EditConfigContext);

    // Get instance section in config
    const instance = config[id];

    // Format IP address as user types in field
    const setIp = (value) => {
        const newIP = formatIp(config[id]["ip"], value);
        handleInputChange(id, "ip", newIP);
    };

    return (
        <InputWrapper label="IP">
            <Form.Control
                type="text"
                value={instance.ip}
                pattern="^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
                onChange={(e) => setIp(e.target.value)}
                isInvalid={(highlightInvalid && !instance.ip)}
            />
        </InputWrapper>
    );
};

IPInput.propTypes = {
    id: PropTypes.string.isRequired
};

export default IPInput;
