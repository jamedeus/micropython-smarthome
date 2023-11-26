import React, { useContext } from 'react';
import Form from 'react-bootstrap/Form';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';


// Get object containing friendly_name: IP pairs for all existing nodes
const context = JSON.parse(document.getElementById("api_target_options").textContent);
const addresses = context.addresses;


function TargetNodeDropdown({ id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    // Handler for target select dropdown
    const change_target_node = (target) => {
        handleInputChange(id, "ip", target);
    }

    return (
        <InputWrapper label="Target Node">
            <Form.Select value={instance.ip} onChange={(e) => change_target_node(e.target.value)}>
                <option disabled>Select target node</option>
                {Object.entries(addresses).map(option => (
                    <option value={option[1]}>{option[0]}</option>
                ))}
            </Form.Select>
        </InputWrapper>
    );
}


export default TargetNodeDropdown;
