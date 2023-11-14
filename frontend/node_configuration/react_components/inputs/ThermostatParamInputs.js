import React from 'react';
import InputWrapper from './InputWrapper';

function ThermostatParamInputs({ key, param, mode, units, tolerance, onChange }) {
    return (
        <>
            <InputWrapper label="Mode">
                <select className="form-select" value={mode} onChange={(e) => onChange("mode", e.target.value)} required>
                    <option value="cool">Cool</option>
                    <option value="heat">Heat</option>
                </select>
            </InputWrapper>

            <InputWrapper label="Units">
                <select className="form-select" value={units} onChange={(e) => onChange("units", e.target.value)} /*oninput="update_thermostat_slider(this);update_config(this);"*/ required>
                    <option value="fahrenheit">Fahrenheit</option>
                    <option value="celsius">Celsius</option>
                    <option value="kelvin">Kelvin</option>
                </select>
            </InputWrapper>

            <InputWrapper label="Tolerance">
                <input type="text" className="form-control thermostat" placeholder="" value={tolerance} onChange={(e) => onChange("tolerance", e.target.value)} required />
            </InputWrapper>
        </>
    );
}

export default ThermostatParamInputs;
