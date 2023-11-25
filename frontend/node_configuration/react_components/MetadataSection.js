import React, { useContext } from 'react';
import Form from 'react-bootstrap/Form';
import { ConfigContext } from './ConfigContext';
import InputWrapper from './inputs/InputWrapper';
import { send_post_request } from './django_util';


function MetadataSection() {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Add invalid highlight when duplicate name entered
    async function prevent_duplicate_friendly_name(event) {
        // Get reference to input, current value
        const el = event.target;
        const new_name = event.target.value;

        // Skip API call if editing and new name matches original name
        if (!edit_existing || new_name.toLowerCase() != orig_name) {
            // Send new name to backend
            const response = await send_post_request('/check_duplicate', {'name': new_name})

            // If name is duplicate add invalid highlight, otherwise remove
            if (!response.ok) {
                el.classList.add('is-invalid');
            } else {
                el.classList.remove('is-invalid');
            }
        }

        // Update state + contents of input regardless of validity
        handleInputChange("metadata", "id", new_name);
    }

    return (
        <div id="metadata">
            <div className="mb-4">
                <h2>Metadata</h2>
                <InputWrapper label="Name">
                    <Form.Control
                        type="text"
                        value={config.metadata.id}
                        onChange={(e) => prevent_duplicate_friendly_name(e)}
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
                    />
                </InputWrapper>
                <InputWrapper label="Floor">
                    <Form.Control
                        type="text"
                        value={config.metadata.floor}
                        onChange={(e) => handleInputChange("metadata", "floor", e.target.value)}
                    />
                </InputWrapper>
            </div>
            <div className="mb-4">
                <h2>Wifi</h2>
                <InputWrapper label="SSID">
                    <Form.Control
                        type="text"
                        id="ssid"
                        value={config.wifi.ssid}
                        onChange={(e) => handleInputChange("wifi", "ssid", e.target.value)}
                    />
                </InputWrapper>
                <InputWrapper label="Password">
                    <Form.Control
                        type="password"
                        id="password"
                        value={config.wifi.password}
                        onChange={(e) => handleInputChange("wifi", "password", e.target.value)}
                    />
                </InputWrapper>
            </div>
        </div>
    )
}

export default MetadataSection;
