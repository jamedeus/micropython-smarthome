import React from 'react';
import InputWrapper from './InputWrapper';

function NicknameInput({ key, id, param, value, onChange }) {
    return (
        <InputWrapper label="Nickname">
            <input
                type="text"
                className="form-control nickname"
                placeholder=""
                value={value}
                onChange={(e) => onChange(param, e.target.value)}
                required
            />
        </InputWrapper>
    );
}

export default NicknameInput;
