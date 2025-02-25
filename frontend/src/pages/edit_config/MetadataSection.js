import React, { useContext, useCallback } from 'react';
import Form from 'react-bootstrap/Form';
import { EditConfigContext } from 'root/EditConfigContext';
import InputWrapper from 'inputs/InputWrapper';
import { numbersOnly } from 'util/validation';
import { debounce } from 'util/helper_functions';
import { send_post_request } from 'util/django_util';

const MetadataSection = () => {
    // Get current state + callback functions from context
    const {
        config,
        original_name,
        edit_existing,
        handleInputChange,
        highlightInvalid,
        setHasInvalidFields
    } = useContext(EditConfigContext);

    // Add invalid highlight when duplicate name entered
    const prevent_duplicate_friendly_name = async (event) => {
        // Get reference to input, current value
        const field = event.target;
        const new_name = event.target.value;

        // Update state + contents of input regardless of validity
        handleInputChange("metadata", "id", new_name);

        // Skip API call if editing and new name matches original name
        if (!edit_existing || new_name.toLowerCase() != original_name) {
            check_duplicate(new_name, field);
        }
    };

    // Debounce to prevent API call on every keystroke
    const check_duplicate = useCallback(debounce(async (new_name, field) => {
        // Send new name to backend
        const response = await send_post_request(
            '/check_duplicate',
            {name: new_name}
        );

        // If name is duplicate add red highlight, disable next page button
        if (!response.ok) {
            field.classList.add('is-invalid');
            setHasInvalidFields(true);
            // If name available remove red highlight, enable next page button
        } else {
            field.classList.remove('is-invalid');
            setHasInvalidFields(false);
        }
    }, 200), []);

    // Floor must be positive or negative integer, 3 digits max
    const set_floor = (value) => {
        let input = numbersOnly(value).substring(0,3);
        if (value[0] === '-') {
            input = '-' + input;
        }
        handleInputChange("metadata", "floor", input);
    };

    return (
        <div id="metadata">
            <div className="mb-4 mx-3">
                <InputWrapper label="Name">
                    <Form.Control
                        type="text"
                        value={config.metadata.id}
                        onChange={(e) => prevent_duplicate_friendly_name(e)}
                        isInvalid={(highlightInvalid && !config.metadata.id)}
                    />
                    <Form.Control.Feedback type="invalid">
                        Name must be unique
                    </Form.Control.Feedback>
                </InputWrapper>
                <InputWrapper label="Location">
                    <Form.Control
                        type="text"
                        value={config.metadata.location}
                        onChange={(e) => handleInputChange("metadata", "location", e.target.value)}
                        isInvalid={(highlightInvalid && !config.metadata.location)}
                    />
                </InputWrapper>
                <InputWrapper label="Floor">
                    <Form.Control
                        type="text"
                        value={config.metadata.floor}
                        onChange={(e) => set_floor(e.target.value)}
                        isInvalid={(highlightInvalid && !config.metadata.floor)}
                    />
                </InputWrapper>
            </div>
        </div>
    );
};

export default MetadataSection;
