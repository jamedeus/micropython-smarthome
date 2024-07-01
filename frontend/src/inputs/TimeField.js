import React, { useState, useRef } from 'react';
import PropTypes from 'prop-types';
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

export const TimeField = ({ timestamp, handleChange, schedule_keywords, highlightInvalid }) => {
    // Create state to control popup visibility
    const [visible, setVisible] = useState(false);

    // Create state for timestamp parameters
    // - original_timestamp: Timestamp when popup opened
    // - timestamp: Current timestamp (detect change)
    // - show_keyword: Determines if timestamp input or keyword dropdown shown
    const [timeDetails, setTimeDetails] = useState({
        original_timestamp: timestamp,
        timestamp: timestamp,
        show_keyword: Object.keys(schedule_keywords).includes(timestamp)
    });

    const handleClose = () => {
        // Only update state if timestamp was changed
        if (timeDetails.timestamp !== timeDetails.original_timestamp) {
            handleChange(timeDetails.timestamp, timeDetails.original_timestamp);
        }

        // Close popup
        setVisible(false);
    };

    // Takes timeDetails param name and value, updates and re-renders
    const setParam = (param, value) => {
        setTimeDetails({ ...timeDetails, [param]: value});
    };

    // Reference to span that shows current time, opens popup
    const buttonRef = useRef(null);

    // Add invalid highlight if timestamp is empty and highlightInvalid is true
    const invalid =  highlightInvalid && !timestamp;

    return (
        <div>
            {/* Display current timestamp, open edit popup when clicked */}
            <span
                ref={buttonRef}
                className={`form-control ${invalid ? 'is-invalid' : ''}`}
                onClick={() => setVisible(true)}
            >
                {format12h(timestamp)}
            </span>

            {/* Edit timestamp popup */}
            <PopupDiv
                show={visible}
                anchorRef={buttonRef}
                onClose={handleClose}
            >
                <div className={timeDetails.show_keyword ? "d-none" : ""}>
                    <Form.Label>Time</Form.Label>
                    <Form.Control
                        className="text-center"
                        type="time"
                        value={timeDetails.timestamp}
                        onChange={(e) => setParam("timestamp", e.target.value)}
                        autoFocus
                    />
                </div>
                <div className={timeDetails.show_keyword ? "" : "d-none"}>
                    <Form.Label>Keyword</Form.Label>
                    <Dropdown
                        value={timeDetails.timestamp}
                        options={Object.keys(schedule_keywords)}
                        onChange={(value) => setParam("timestamp", value)}
                    />
                </div>

                <div className="d-flex mt-2">
                    <Form.Check
                        id="keyword-switch"
                        type="switch"
                        label="Keyword"
                        checked={timeDetails.show_keyword}
                        onChange={(e) => setParam("show_keyword", e.target.checked)}
                    />
                </div>
            </PopupDiv>
        </div>
    );
};

TimeField.propTypes = {
    timestamp: PropTypes.string,
    handleChange: PropTypes.func,
    schedule_keywords: PropTypes.object,
    highlightInvalid: PropTypes.bool
};
