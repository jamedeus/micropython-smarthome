import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';
import { api_target_options } from './../django_util';

// Get object containing friendly_name: IP pairs for all existing nodes
const addresses = api_target_options.addresses;

function TargetNodeDropdown({ id }) {
    // Get curent state + callback functions from context
    const { config, handleInstanceUpdate, highlightInvalid } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    // Handler for target select dropdown
    const change_target_node = (target) => {
        handleInstanceUpdate(id, { ...instance, ["ip"]: target, ["default_rule"]: ""})
    }

    return (
        <InputWrapper label="Target Node">
            <Form.Select
                value={instance.ip}
                onChange={(e) => change_target_node(e.target.value)}
                isInvalid={(highlightInvalid && !instance.ip)}
            >
                <option value="">Select target node</option>
                {Object.entries(addresses).map(option => (
                    <option key={option[1]} value={option[1]}>{option[0]}</option>
                ))}
            </Form.Select>
        </InputWrapper>
    );
}

TargetNodeDropdown.propTypes = {
    id: PropTypes.string
}

export default TargetNodeDropdown;
