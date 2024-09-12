import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import InputWrapper from 'inputs/InputWrapper';
import { EditConfigContext } from 'root/EditConfigContext';

const ModeSelectDropdown = ({ id, options }) => {
    // Get current config state, callback to change mode, highlightInvalid bool
    const {
        config,
        handleInputChange,
        highlightInvalid
    } = useContext(EditConfigContext);

    // Return dropdown with correct mode selected
    // Add red highlight if highlightInvalid is true and mode not selected
    return (
        <InputWrapper label={"Mode"}>
            <Form.Select
                value={config[id]["mode"]}
                onChange={(e) => handleInputChange(id, "mode", e.target.value)}
                isInvalid={highlightInvalid && !config[id]["mode"]}
            >
                <option value="">Select mode</option>
                {options.map(option => (
                    <option
                        key={option}
                        value={option}
                    >
                        {option}
                    </option>
                ))}
            </Form.Select>
        </InputWrapper>
    );
};

ModeSelectDropdown.propTypes = {
    id: PropTypes.string.isRequired,
    options: PropTypes.array.isRequired
};

export default ModeSelectDropdown;
