import React, { useContext } from 'react';
import Form from 'react-bootstrap/Form';
import { ConfigContext } from './ConfigContext';
import InputWrapper from './inputs/InputWrapper';

function MetadataSection() {
    // Get curent state + callback functions from context
    const { config, handleInputChange } = useContext(ConfigContext);

    return (
        <div id="metadata">
            <div className="mb-4">
                <h2>Metadata</h2>
                <InputWrapper label="Name">
                    <Form.Control
                        type="text"
                        value={config.metadata.id}
                        onChange={(e) => handleInputChange("metadata", "id", e.target.value)}
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
