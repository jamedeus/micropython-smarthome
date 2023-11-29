import React, { useRef, useEffect } from 'react';
import PropTypes from 'prop-types';

const PopupDiv = ({ children, show, anchorRef, onClose }) => {
    const popupRef = useRef(null);

    useEffect(() => {
        // Closes popup if user clicks outside popup div
        const handleClickOutside = (event) => {
            if (popupRef.current && !popupRef.current.contains(event.target)) {
                console.log("Clicked outside, closing")
                onClose();
            }
        };

        // Runs when popup shown
        if (show) {
            console.log("Adding listener")
            // Add listener to close popup if user clicks outside div
            document.addEventListener("mousedown", handleClickOutside);

            // Set same width as parent element with 20px margin
            if (popupRef.current && anchorRef.current) {
                const { width } = anchorRef.current.getBoundingClientRect();
                popupRef.current.style.width = `${width - 40}px`;
            }
        }

        // Remove listener when closed
        return () => {
            console.log("Removing listener")
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [show, onClose]);

    if (!show) {
        return null;
    }

    return (
        <div ref={popupRef} className="schedule-rule-param-popup">
            {children}
        </div>
    );
};

PopupDiv.propTypes = {
    children: PropTypes.node,
    show: PropTypes.bool,
    anchorRef: PropTypes.object,
    onClose: PropTypes.func
}

export default PopupDiv;
