import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import { ConfigContext } from './../ConfigContext';
import InputWrapper from './InputWrapper';
import { convert_temperature } from './../thermostat_util';
import Dropdown from './Dropdown';

function ThermostatParamInputs({ id }) {
    // Get curent state + callback functions from context
    const { config, highlightInvalid, handleInputChange, handleInstanceUpdate } = useContext(ConfigContext);

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
            }
            handleInputChange(id, "tolerance", input);
        }
    }

    const changeUnits = (newUnits) => {
        // Save old units for conversions
        const oldUnits = instance.units;

        // Convert default_rule to new units
        const newRule = convert_temperature(instance.default_rule, oldUnits, newUnits);

        // Copy state object, add new rule + new units
        const update = { ...instance, ["default_rule"]: newRule, ["units"]: newUnits};

        // Convert all schedule rules to new units
        for (let rule in instance.schedule) {
            if (/^-?\d+(\.\d+)?$/.test(instance.schedule[rule])) {
                const newRule = convert_temperature(instance.schedule[rule], oldUnits, newUnits);
                instance.schedule[rule] = newRule;
            }
        }

        // Update units and rules in state object
        handleInstanceUpdate(id, update);
    }

    const changeMode = (newMode) => {
        handleInputChange(id, "mode", newMode);
    }

    return (
        <>
            <Dropdown
                value={instance.mode}
                options={["Cool", "Heat"]}
                onChange={changeMode}
                label="Mode"
                isInvalid={highlightInvalid && !instance.mode}
            />

            <Dropdown
                value={instance.units}
                options={["Celsius", "Fahrenheit", "Kelvin"]}
                onChange={changeUnits}
                label="Units"
                isInvalid={highlightInvalid && !instance.units}
            />

            <InputWrapper label="Tolerance">
                <Form.Control
                    type="text"
                    value={instance.tolerance}
                    onChange={(e) => setTolerance(e.target.value)}
                    isInvalid={highlightInvalid && !instance.tolerance}
                />
            </InputWrapper>
        </>
    );
}

ThermostatParamInputs.propTypes = {
    id: PropTypes.string
}

export default ThermostatParamInputs;
