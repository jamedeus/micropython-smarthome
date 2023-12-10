import React from 'react';
import PropTypes from 'prop-types';
import 'css/animations.css';

export const LoadingSpinner = ({ size }) => {
    switch(size) {
        case "large":
            return (
                <div id="spinner" className="loading-animation loading-animation-lg m-auto">
                    <div></div><div></div><div></div><div></div>
                </div>
            );
        case "medium":
            return (
                <div id="spinner" className="loading-animation loading-animation-md m-auto">
                    <div></div><div></div><div></div><div></div>
                </div>
            );
        case "small":
            return (
                <div id="spinner" className="loading-animation loading-animation-sm m-auto">
                    <div></div><div></div><div></div><div></div>
                </div>
            );
    }
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
