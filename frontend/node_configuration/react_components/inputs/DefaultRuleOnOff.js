import React, { useContext } from 'react';
import Form from 'react-bootstrap/Form';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';

function DefaultRuleOnOff({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    return (
        <InputWrapper label="Default Rule">
            <Form.Select value={instance.default_rule} onChange={(e) => handleInputChange(id, "default_rule", e.target.value)}>
                <option disabled>Select default rule</option>
                <option value="on">On</option>
                <option value="off">Off</option>
            </Form.Select>
        </InputWrapper>
    );
}

export default DefaultRuleOnOff;
