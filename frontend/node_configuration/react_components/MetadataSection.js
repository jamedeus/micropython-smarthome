import React, { useContext } from 'react';
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
                    <input
                        type="text"
                        className="form-control"
                        defaultValue={config.metadata.id}
                        placeholder=""
                        aria-describedby="friendlyName-feedback"
                        onChange={(e) => handleInputChange("metadata", "id", e.target.value)}
                        required=""
                    />
                    <div id="friendlyName-feedback" className="invalid-feedback">
                        Name must be unique
                    </div>
                </InputWrapper>
                <InputWrapper label="Location">
                    <input
                        type="text"
                        className="form-control"
                        placeholder=""
                        defaultValue={config.metadata.location}
                        onChange={(e) => handleInputChange("metadata", "location", e.target.value)}
                        required=""
                    />
                </InputWrapper>
                <InputWrapper label="Floor">
                    <input
                        type="text"
                        className="form-control"
                        placeholder=""
                        defaultValue={config.metadata.floor}
                        onChange={(e) => handleInputChange("metadata", "floor", e.target.value)}
                        required=""
                    />
                </InputWrapper>
            </div>
            <div className="mb-4">
                <h2>Wifi</h2>
                <InputWrapper label="SSID">
                    <input
                        type="text"
                        className="form-control"
                        id="ssid"
                        placeholder=""
                        defaultValue={config.wifi.ssid}
                        onChange={(e) => handleInputChange("wifi", "ssid", e.target.value)}
                        required=""
                    />
                </InputWrapper>
                <InputWrapper label="Password">
                    <input
                        type="password"
                        className="form-control"
                        id="password"
                        placeholder=""
                        defaultValue={config.wifi.password}
                        onChange={(e) => handleInputChange("wifi", "password", e.target.value)}
                        required=""
                    />
                </InputWrapper>
            </div>
        </div>
    )
}

export default MetadataSection;
