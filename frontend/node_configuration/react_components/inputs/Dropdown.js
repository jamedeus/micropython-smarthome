import React from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import InputWrapper from './InputWrapper';

// Takes string, returns with first character of each word capitalized
function toTitle(str) {
    return str.replace(/\w\S*/g, function(txt){
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
}

function Dropdown({ value, options, onChange, label="", isInvalid=false }) {
    switch(true) {
        // Add InputWrapper if label given
        case label.length > 0:
            return (
                <InputWrapper label={toTitle(label)}>
                    <Form.Select
                        value={value}
                        onChange={(e) => onChange(e.target.value)}
                        isInvalid={isInvalid}
                    >
                        <option value="">Select {label.toLowerCase()}</option>
                        {options.map(option => (
                            <option key={option} value={option.toLowerCase()}>{toTitle(option)}</option>
                        ))}
                    </Form.Select>
                </InputWrapper>
            );
        // No wrapper if label blank
        case label.length === 0:
            return (
                <Form.Select
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    isInvalid={isInvalid}
                >
                    {options.map(option => (
                        <option key={option} value={option.toLowerCase()}>{toTitle(option)}</option>
                    ))}
                </Form.Select>
            );
    }
}

Dropdown.propTypes = {
    value: PropTypes.string,
    options: PropTypes.array,
    onChange: PropTypes.func,
    label: PropTypes.string,
    isInvalid: PropTypes.bool
};

export default Dropdown;
