import React from 'react';
import InputWrapper from './InputWrapper';

function DefaultRuleOnOff({ id, value, onChange }) {
    return (
        <InputWrapper label="Default Rule">
            <select className="form-select" value={value} autoComplete="off" onChange={(e) => onChange(id, e.target.value)} required>
                <option disabled>Select default rule</option>
                <option value="on">On</option>
                <option value="off">Off</option>
            </select>
        </InputWrapper>
    );
}

export default DefaultRuleOnOff;
