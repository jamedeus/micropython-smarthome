import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import InputWrapper from 'inputs/InputWrapper';
import { ConfigContext } from 'root/ConfigContext';

const PinSelectDropdown = ({ id, options }) => {
    // Get current config state, callback to change pin, highlightInvalid bool
    const { config, handleInputChange, highlightInvalid } = useContext(ConfigContext);

    // Get array of all pins used by other instances
    let usedPins = [];
    Object.entries(config).forEach(([instance, params]) => {
        if (instance !== id && params.pin !== undefined) {
            usedPins.push(String(params.pin));
        }
    });

    // Set value to empty string if config section missing (ir_blaster removed)
    const value = config[id] ? config[id]["pin"] : '';

    // Add invalid highlight if state is true, config section exists, and pin
    // is missing from config section
    const invalid = highlightInvalid && config[id] && !config[id]["pin"];

    // Return dropdown with correct pin selected, used pins disabled
    // Add red highlight if highlightInvalid is true and pin not selected
    return (
        <InputWrapper label="Pin">
            <Form.Select
                value={value}
                onChange={(e) => handleInputChange(id, "pin", e.target.value)}
                isInvalid={invalid}
            >
                <option value="">Select pin</option>
                {options.map(option => (
                    <option
                        key={option}
                        value={option}
                        disabled={usedPins.includes(option)}
                    >
                        {option}
                    </option>
                ))}
            </Form.Select>
        </InputWrapper>
    );
};

PinSelectDropdown.propTypes = {
    id: PropTypes.string.isRequired,
    options: PropTypes.array.isRequired
};

export default PinSelectDropdown;
