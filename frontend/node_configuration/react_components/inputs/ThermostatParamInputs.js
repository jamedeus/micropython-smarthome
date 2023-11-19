import React, { useContext } from 'react';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';

function ThermostatParamInputs({ key, id }) {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Get instance section in config
    const instance = config[id];

    return (
        <>
            <InputWrapper label="Mode">
                <select className="form-select" value={instance.mode} onChange={(e) => handleInputChange(id, "mode", e.target.value)} required>
                    <option value="cool">Cool</option>
                    <option value="heat">Heat</option>
                </select>
            </InputWrapper>

            <InputWrapper label="Units">
                <select className="form-select" value={instance.units} onChange={(e) => handleInputChange(id, "units", e.target.value)} /*oninput="update_thermostat_slider(this);update_config(this);"*/ required>
                    <option value="fahrenheit">Fahrenheit</option>
                    <option value="celsius">Celsius</option>
                    <option value="kelvin">Kelvin</option>
                </select>
            </InputWrapper>

            <InputWrapper label="Tolerance">
                <input type="text" className="form-control thermostat" placeholder="" value={instance.tolerance} onChange={(e) => handleInputChange(id, "tolerance", e.target.value)} required />
            </InputWrapper>
        </>
    );
}

export default ThermostatParamInputs;
