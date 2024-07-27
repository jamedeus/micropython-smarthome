import React, { useRef, useEffect } from 'react';
import PropTypes from 'prop-types';

const PopupDiv = ({ children, show, onClose }) => {
    const popupRef = useRef(null);

    // Closes popup if user clicks outside popup div
    const handleClickOutside = (event) => {
        if (popupRef.current && !popupRef.current.contains(event.target)) {
            onClose();
        }
    };

    useEffect(() => {
        // Add listener when popup shown
        if (show) {
            // Add listener to close popup if user clicks outside div
            document.addEventListener("mousedown", handleClickOutside);
        }

        // Remove listener when closed
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [show, onClose]);

    if (show) {
        return (
            <div
                ref={popupRef}
                className="schedule-rule-param-popup border border-3"
            >
                {children}
            </div>
        );
    } else {
        return null;
    }
};

PopupDiv.propTypes = {
    children: PropTypes.node.isRequired,
    show: PropTypes.bool.isRequired,
    onClose: PropTypes.func.isRequired
};

export default PopupDiv;
