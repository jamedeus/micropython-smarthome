import React, { useContext } from 'react';
import Form from 'react-bootstrap/Form';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';
import { convert_temperature } from './../thermostat_util';


function ThermostatParamInputs({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange, handleInstanceUpdate } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    const setTolerance = (value) => {
        if (value.endsWith('.')) {
            handleInputChange(id, "tolerance", value);
        } else {

            // Remove everything except digits and period, 4 digit max
            let input = parseFloat(value.replace(/[^\d.]/g, '').substring(0,4));
            // Constrain to 0.1 - 10.0 degrees
            input = Math.max(0.1, Math.min(input, 10));
            if (isNaN(input)) {
                input = "";
            };
            handleInputChange(id, "tolerance", input);
        };
    }

    // Get "temperture.toFixed(1) is not a function", prob gets NaN or something?
    const changeUnits = (newUnits) => {
        // Convert default_rule to new units
        const newRule = convert_temperature(instance.default_rule, instance.units, newUnits);
        // Copy state object, add new rule
        const update = { ...instance, ["default_rule"]: newRule };
        update["units"] = newUnits;
        // Update units and default_rule in state object
        handleInstanceUpdate(id, update);
    }

    return (
        <>
            <InputWrapper label="Mode">
                <Form.Select value={instance.mode} onChange={(e) => handleInputChange(id, "mode", e.target.value)}>
                    <option value="cool">Cool</option>
                    <option value="heat">Heat</option>
                </Form.Select>
            </InputWrapper>

            <InputWrapper label="Units">
                <Form.Select value={instance.units} onChange={(e) => changeUnits(e.target.value)}>
                    <option value="celsius">Celsius</option>
                    <option value="fahrenheit">Fahrenheit</option>
                    <option value="kelvin">Kelvin</option>
                </Form.Select>
            </InputWrapper>

            <InputWrapper label="Tolerance">
                <Form.Control
                    type="text"
                    value={instance.tolerance}
                    onChange={(e) => setTolerance(e.target.value)}
                />
            </InputWrapper>
        </>
    );
}

export default ThermostatParamInputs;
