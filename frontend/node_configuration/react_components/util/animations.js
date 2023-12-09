import React from 'react';
import PropTypes from 'prop-types';

export const LoadingSpinner = () => {
    return (
        <div className="spinner-border mx-auto" style={{width: "3rem", height: "3rem"}} role="status">
            <span className="visually-hidden">Loading...</span>
        </div>
    );
};

export const ButtonSpinner = () => {
    return (
        <div id="spinner" className="loading-animation loading-animation-show m-auto">
            <div></div><div></div><div></div><div></div>
        </div>
    );
};

export const CheckmarkAnimation = ({ size="large" }) => {
    switch(size) {
        case "large":
            return (
                <svg className="checkmark mx-auto" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                    <circle className="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
                    <path className="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                </svg>
            );
        case "small":
            return (
                <svg className="checkmark_sm mx-auto" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                    <circle className="checkmark__circle_sm" cx="26" cy="26" r="25" fill="none"/>
                    <path className="checkmark__check_sm" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                </svg>
            );
    }
};

CheckmarkAnimation.propTypes = {
    size: PropTypes.string
};
