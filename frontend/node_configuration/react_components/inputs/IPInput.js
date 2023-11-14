import React from 'react';
import InputWrapper from './InputWrapper';

function IPInput({ key, param, value, onChange }) {
    return (
        <InputWrapper label="IP">
            <input
                type="text"
                className="form-control ip-input validate"
                placeholder=""
                value={value}
                pattern="^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
                onChange={(e) => onChange(param, e.target.value)}
                required
            />
        </InputWrapper>
    );
}

export default IPInput;
