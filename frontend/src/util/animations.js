import React from 'react';
import PropTypes from 'prop-types';
import 'css/LoadingSpinner.css';
import 'css/CheckmarkAnimation.css';


export const LoadingSpinner = ({ size, classes=[] }) => {
    let classList = ["loading-animation", "m-auto"].concat(classes);

    switch(size) {
        case "large":
            classList.push("loading-animation-lg");
            break;
        case "medium":
            classList.push("loading-animation-md");
            break;
        case "small":
            classList.push("loading-animation-sm");
            break;
    }

    return (
        <div id="spinner" className={classList.join(" ")}>
            <div></div><div></div><div></div><div></div>
        </div>
    );
};

LoadingSpinner.propTypes = {
    size: PropTypes.string,
    classes: PropTypes.array
};


export const CheckmarkAnimation = ({ size, color, classes=[] }) => {
    let classList = ["checkmark", "m-auto"].concat(classes);

    switch(size) {
        case "large":
            classList.push("checkmark-lg");
            break;
        case "small":
            classList.push("checkmark-sm");
            break;
    }

    switch(color) {
        case "green":
            classList.push("checkmark-green");
            break;
        case "white":
            classList.push("checkmark-white");
            break;
    }

    return (
        <svg className={classList.join(" ")} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
            <circle className="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
            <path className="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
        </svg>
    );
};

CheckmarkAnimation.propTypes = {
    size: PropTypes.string,
    color: PropTypes.string,
    classes: PropTypes.array
};
