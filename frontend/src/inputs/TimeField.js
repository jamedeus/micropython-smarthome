import React, { useState, useRef, useContext } from 'react';
import PropTypes from 'prop-types';
import { ConfigContext } from 'root/ConfigContext';
import Form from 'react-bootstrap/Form';
import PopupDiv from './PopupDiv';
import Dropdown from 'inputs/Dropdown.js';

// Used to identify HH:MM timestamp
const timestamp_regex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;

// Takes 24h timestamp, returns 12h with am/pm suffix
function format12h(timestamp) {
    // Return placeholder string if timestamp empty
    if (!timestamp) {
        return 'Set time';
    }

    // Return keywords unchanged
    if ( ! timestamp_regex.test(timestamp)) {
        return timestamp;
    }

    let [hour, minute] = timestamp.split(':');
    const suffix = parseInt(hour) >= 12 ? 'pm' : 'am';
    // Convert to 12h format, if midnight replace 0 with 12
    hour = parseInt(hour) % 12;
    hour = hour === 0 ? 12 : hour;
    return `${hour}:${minute} ${suffix}`;
}

export const TimeField = ({ instance, timestamp, schedule_keywords, highlightInvalid }) => {
    // Get curent state from context
    const { config, handleInputChange } = useContext(ConfigContext);

    // Create state for popup visibility, contents
    const [popupContent, setPopupContent] = useState({
        visible: false,
        instance: '',
        original_timestamp: '',
        timestamp: '',
        show_keyword: false
    });

    // Takes timestamp, returns true if matches existing keyword, otherwise False
    function isKeyword(timestamp) {
        return Object.keys(schedule_keywords).includes(timestamp);
    }

    const handleShow = () => {
        // Replace popupContent with params for selected rule
        let update = {
            visible: true,
            instance: instance,
            original_timestamp: timestamp,
            timestamp: timestamp,
            show_keyword: isKeyword(timestamp)
        };

        // Set modal contents, show
        setPopupContent(update);
    };

    const handleClose = () => {
        // Get existing rules
        const rules = { ...config[popupContent.instance]["schedule"] };

        // Get value of rule being edited
        const rule_value = rules[popupContent.original_timestamp];

        // If timestamp was changed, delete original rule before adding
        if (popupContent.timestamp !== popupContent.original_timestamp) {
            delete rules[popupContent.original_timestamp];
        }

        // Add new rule, update state object, close modal
        rules[popupContent.timestamp] = rule_value;
        handleInputChange(popupContent.instance, "schedule", rules);
        setPopupContent({ ...popupContent, ["visible"]: false});
    };

    // Takes popupContent param name and value, updates and re-renders
    const set_popup_param = (param, value) => {
        setPopupContent({ ...popupContent, [param]: value});
    };

    // Reference to span that shows current time, opens popup
    const buttonRef = useRef(null);

    // Add invalid highlight if timestamp is empty and highlightInvalid is true
    let invalid = false;
    if (highlightInvalid && !timestamp) {
        invalid = true;
    }

    return (
        <div>
            {/* Display current timestamp, open edit popup when clicked */}
            <span
                ref={buttonRef}
                className={`form-control ${invalid ? 'is-invalid' : ''}`}
                onClick={() => handleShow()}
            >
                {format12h(timestamp)}
            </span>

            {/* Edit timestamp popup */}
            <PopupDiv show={popupContent.visible} anchorRef={buttonRef} onClose={handleClose}>
                <>
                    <div id="timestamp-input" className={popupContent.show_keyword === true ? "d-none" : ""}>
                        <Form.Label>Time</Form.Label>
                        <Form.Control
                            className="text-center"
                            type="time"
                            value={popupContent.timestamp}
                            onChange={(e) => set_popup_param("timestamp", e.target.value)}
                            autoFocus
                        />
                    </div>
                    <div id="keyword-input" className={popupContent.show_keyword === false ? "d-none" : ""}>
                        <Form.Label>Keyword</Form.Label>
                        <Dropdown
                            value={popupContent.timestamp}
                            options={Object.keys(schedule_keywords)}
                            onChange={(value) => set_popup_param("timestamp", value)}
                        />
                    </div>

                    <div className="d-flex mt-2">
                        <Form.Check
                            id="keyword-switch"
                            type="switch"
                            label="Keyword"
                            checked={popupContent.show_keyword}
                            onChange={(e) => set_popup_param("show_keyword", e.target.checked)}
                        />
                    </div>
                </>
            </PopupDiv>
        </div>
    );
};

TimeField.propTypes = {
    instance: PropTypes.string,
    timestamp: PropTypes.string,
    schedule_keywords: PropTypes.object,
    highlightInvalid: PropTypes.bool
};
