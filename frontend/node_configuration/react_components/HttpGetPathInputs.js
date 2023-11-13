import React from 'react';
import InputWrapper from './InputWrapper';

function HttpGetPathInputs({ id, on_path, off_path, onChange }) {
    return (
        <>
            <InputWrapper label="On path">
                <input
                    type="text"
                    className="form-control validate"
                    placeholder="Appended to URI for on action"
                    value={on_path}
                    onChange={(e) => onChange(e.target.value)}
                    required
                />
            </InputWrapper>

            <InputWrapper label="Off path">
                <input
                    type="text"
                    className="form-control validate"
                    placeholder="Appended to URI for off action"
                    value={off_path}
                    onChange={(e) => onChange(e.target.value)}
                    required
                />
            </InputWrapper>
        </>
    );
}

export default HttpGetPathInputs;
