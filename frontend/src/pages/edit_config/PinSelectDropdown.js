import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import InputWrapper from 'inputs/InputWrapper';
import { EditConfigContext } from 'root/EditConfigContext';

const PinSelectDropdown = ({ id, options, label="Pin", param="pin" }) => {
    // Get current config state, callback to change pin, highlightInvalid bool
    const {
        config,
        handleInputChange,
        highlightInvalid
    } = useContext(EditConfigContext);

    // Get array of all pins in config except the one controlled by this input
    // (don't disable currently selected option if dropdown opened again)
    let usedPins = [];
    Object.entries(config).forEach(([instance, params]) => {
        // Add all pin attributes used by other instances
        if (instance !== id && params.pin !== undefined) {
            usedPins.push(String(params.pin));
        }
        // Add all pin_* attributes used by other instances + pin_* attributes
        // used by this instance (except the one controlled by this input)
        Object.keys(params).forEach((key) => {
            if (key.startsWith('pin_') && !(instance === id && key === param)) {
                usedPins.push(String(params[key]));
            }
        });
    });

    // Set value to empty string if config section missing (ir_blaster removed)
    const value = config[id] ? config[id][param] : '';

    // Add invalid highlight if state is true, config section exists, and pin
    // is missing from config section
    const invalid = highlightInvalid && config[id] && !config[id][param];

    // Return dropdown with correct pin selected, used pins disabled
    // Add red highlight if highlightInvalid is true and pin not selected
    return (
        <InputWrapper label={label}>
            <Form.Select
                value={value}
                onChange={(e) => handleInputChange(id, param, e.target.value)}
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
    options: PropTypes.array.isRequired,
    label: PropTypes.string,
    param: PropTypes.string
};

export default PinSelectDropdown;
