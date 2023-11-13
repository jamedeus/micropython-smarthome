import React from 'react';
import InputWrapper from './InputWrapper';

function URIInput({ id, value, onChange }) {
    return (
        <InputWrapper label="URI">
            <input
                type="text"
                className="form-control validate"
                placeholder="IP address or URL"
                value={value}
                pattern="(?:(?:http|https):\/\/)?(?:\S+(?::\S*)?@)?(?:(?:[0-9]{1,3}\.){3}[0-9]{1,3})(?::\d{1,5})?|(?:(?:http|https):\/\/)?[a-zA-Z0-9.]+(?:-[a-zA-Z0-9]+)*(?:\.[a-zA-Z]{2,6})+(?:\/\S*)?"
                onChange={(e) => onChange(id, e.target.value)}
                required
            />
        </InputWrapper>
    );
}

export default URIInput;
