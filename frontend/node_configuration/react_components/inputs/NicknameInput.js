import React from 'react';
import InputWrapper from './InputWrapper';

function NicknameInput({ id, value, onChange }) {
    return (
        <InputWrapper label="Nickname">
            <input
                type="text"
                className="form-control nickname"
                placeholder=""
                value={value}
                onChange={(e) => onChange(id, e.target.value)}
                required
            />
        </InputWrapper>
    );
}

export default NicknameInput;
