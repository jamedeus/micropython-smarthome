import React from 'react';
import PropTypes from 'prop-types';

const InputWrapper = ({ children, label }) => {
    return (
        <div className="mb-2">
            <label className="w-100 fw-bold">
                {label}:
                {children}
            </label>
        </div>
    );
};

InputWrapper.propTypes = {
    children: PropTypes.node.isRequired,
    label: PropTypes.string.isRequired
};

export default InputWrapper;
