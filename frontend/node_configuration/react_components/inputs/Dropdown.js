import React from 'react';
import Form from 'react-bootstrap/Form';
import InputWrapper from './InputWrapper';


// Takes string, returns with first character of each word capitalized
function toTitle(str) {
    return str.replace(/\w\S*/g, function(txt){
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
}


function Dropdown({ value, options, onChange, label="" }) {
    switch(true) {
        // Add InputWrapper if label given
        case label.length > 0:
            return (
                <InputWrapper label={toTitle(label)}>
                    <Form.Select value={value} onChange={(e) => onChange(e.target.value)}>
                        <option disabled>Select {label.toLowerCase()}</option>
                        {options.map(option => (
                            <option value={option.toLowerCase()}>{toTitle(option)}</option>
                        ))}
                    </Form.Select>
                </InputWrapper>
            );
        // No wrapper if label blank
        case label.length === 0:
            return (
                <Form.Select value={value} onChange={(e) => onChange(e.target.value)}>
                    {options.map(option => (
                        <option value={option.toLowerCase()}>{toTitle(option)}</option>
                    ))}
                </Form.Select>
            );
    }
}

export default Dropdown;
