import React from 'react';
import Form from 'react-bootstrap/Form';
import InputWrapper from './InputWrapper';


// Used by SensorPinSelect and DevicePinSelect components
function PinSelectDropdown({id, config, selected, onChange, options}) {
    // Get array of all pins used by other instances
    let usedPins = []
    for (const section in config) {
        if (section !== id && config[section]["pin"] !== undefined) {
            usedPins.push(config[section]["pin"]);
        }
    }

    // Return dropdown with correct pin selected, used pins disabled
    return (
        <InputWrapper label="Pin">
            <Form.Select value={selected} onChange={(e) => onChange(e.target.value)}>
                <option>Select pin</option>
                {options.map(option => (
                    <option value={option} disabled={usedPins.includes(option)}>
                        {option}
                    </option>
                ))}
            </Form.Select>
        </InputWrapper>
    );
}

export default PinSelectDropdown;
