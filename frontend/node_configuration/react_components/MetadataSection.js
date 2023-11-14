import React from 'react';
import InputWrapper from './inputs/InputWrapper';

function MetadataSection({ key, id, floor, location, ssid, password, onChange }) {
    return (
        <div id="metadata">
            <div className="mb-4">
                <h2>Metadata</h2>
                <InputWrapper label="Name">
                    <input
                        type="text"
                        className="form-control"
                        defaultValue={id}
                        placeholder=""
                        aria-describedby="friendlyName-feedback"
                        onChange={(e) => onChange("metadata", "id", e.target.value)}
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
                        defaultValue={location}
                        onChange={(e) => onChange("metadata", "location", e.target.value)}
                        required=""
                    />
                </InputWrapper>
                <InputWrapper label="Floor">
                    <input
                        type="text"
                        className="form-control"
                        placeholder=""
                        defaultValue={floor}
                        onChange={(e) => onChange("metadata", "floor", e.target.value)}
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
                        defaultValue={ssid}
                        onChange={(e) => onChange("wifi", "ssid", e.target.value)}
                        required=""
                    />
                </InputWrapper>
                <InputWrapper label="Password">
                    <input
                        type="password"
                        className="form-control"
                        id="password"
                        placeholder=""
                        defaultValue={password}
                        onChange={(e) => onChange("wifi", "password", e.target.value)}
                        required=""
                    />
                </InputWrapper>
            </div>
        </div>
    )
}

export default MetadataSection;
