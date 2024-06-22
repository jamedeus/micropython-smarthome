import React from 'react';
import PropTypes from 'prop-types';

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

InputWrapper.propTypes = {
    children: PropTypes.node,
    label: PropTypes.string
};

export default InputWrapper;
