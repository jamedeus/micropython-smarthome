import React, { useState } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import PopupDiv from './PopupDiv';
import Dropdown from 'inputs/Dropdown.js';

// Used to identify HH:MM timestamp
const timestamp_regex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;

// Takes 24h timestamp, returns 12h with am/pm suffix
function format12h(timestamp) {
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

    // Handler for timestamp input and keyword dropdown
    const setTimestamp = (newTimestamp) => {
        setTimeDetails({ ...timeDetails, timestamp: newTimestamp});
    };

    // Handler for keyword switch, takes bool
    const showKeyword = (show) => {
        if (show) {
            // Set timestamp to first keyword option (first can't be selected
            // otherwise, timestamp only updates when user changes dropdown
            setTimeDetails({ ...timeDetails,
                timestamp: Object.keys(schedule_keywords)[0],
                show_keyword: true
            });
        } else {
            // Clear timestamp when switching back to time input
            setTimeDetails({ ...timeDetails,
                timestamp: '',
                show_keyword: false
            });
        }
    };

    // Call parent handler, close popup
    const handleClose = () => {
        handleChange(timeDetails.timestamp, timeDetails.original_timestamp);
        setVisible(false);
    };

    // Add invalid highlight if timestamp is empty and highlightInvalid is true
    const invalid =  highlightInvalid && !timestamp;

    return (
        <div>
            {/* Display current timestamp, open edit popup when clicked */}
            <span
                className={`form-control ${invalid ? 'is-invalid' : ''}`}
                onClick={() => setVisible(true)}
            >
                {timestamp ? format12h(timestamp) : 'Set time'}
            </span>

            {/* Edit timestamp popup */}
            <PopupDiv
                show={visible}
                onClose={handleClose}
            >
                {timeDetails.show_keyword ? (
                    <div>
                        <Form.Label>Keyword</Form.Label>
                        <Dropdown
                            value={timeDetails.timestamp}
                            options={Object.keys(schedule_keywords)}
                            onChange={(value) => setTimestamp(value)}
                            focus={true}
                        />
                    </div>
                ) : (
                    <div>
                        <Form.Label>Time</Form.Label>
                        <Form.Control
                            className="text-center"
                            type="time"
                            value={timeDetails.timestamp}
                            onChange={(e) => setTimestamp(e.target.value)}
                            autoFocus
                        />
                    </div>
                )}

                <div className="d-flex mt-2">
                    <Form.Check
                        id="keyword-switch"
                        type="switch"
                        label="Keyword"
                        checked={timeDetails.show_keyword}
                        onChange={(e) => showKeyword(e.target.checked)}
                    />
                </div>
            </PopupDiv>
        </div>
    );
};

TimeField.propTypes = {
    timestamp: PropTypes.string.isRequired,
    handleChange: PropTypes.func.isRequired,
    schedule_keywords: PropTypes.object.isRequired,
    highlightInvalid: PropTypes.bool
};
