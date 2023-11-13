import React from 'react';

function InputWrapper({ children, label }) {
    return (
        <div className="mb-2">
            <label className="w-100">
                <b>{label}:</b>
                {children}
            </label>
        </div>
    );
}

export default InputWrapper;
