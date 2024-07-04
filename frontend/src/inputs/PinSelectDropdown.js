import React from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import InputWrapper from './InputWrapper';

// Used by SensorPinSelect and DevicePinSelect components
function PinSelectDropdown({id, config, selected, onChange, options, isInvalid}) {
    // Get array of all pins used by other instances
    let usedPins = [];
    Object.entries(config).forEach(([instance, params]) => {
        if (instance !== id && params.pin !== undefined) {
            usedPins.push(String(params.pin));
        }
    });

    // Return dropdown with correct pin selected, used pins disabled
    return (
        <InputWrapper label="Pin">
            <Form.Select
                value={selected}
                onChange={(e) => onChange(e.target.value)}
                isInvalid={isInvalid}
            >
                <option value="">Select pin</option>
                {options.map(option => (
                    <option key={option} value={option} disabled={usedPins.includes(option)}>
                        {option}
                    </option>
                ))}
            </Form.Select>
        </InputWrapper>
    );
}

PinSelectDropdown.propTypes = {
    id: PropTypes.string,
    config: PropTypes.object,
    selected: PropTypes.PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string
    ]),
    onChange: PropTypes.func,
    options: PropTypes.array,
    isInvalid: PropTypes.bool
};

export default PinSelectDropdown;
