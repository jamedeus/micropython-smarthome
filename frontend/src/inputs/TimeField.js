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

export const TimeField = ({ timestamp, setTimestamp, schedule_keywords, highlightInvalid, handleClose=() => {} }) => {
    // Create state to control popup visibility
    const [visible, setVisible] = useState(false);

    // Create state to control if timestamp input or keyword dropdown shown
    const [showKeyword, setShowKeyword] = useState(
        Object.keys(schedule_keywords).includes(timestamp)
    );

    // Handler for keyword switch
    const toggleKeyword = () => {
        // Clear timestamp when switching from keyword to time input
        if (showKeyword) {
            setTimestamp('');
        // Set timestamp to first option when switching to dropdown (can't be
        // selected otherwise, timestamp only updates when selection changes)
        } else {
            setTimestamp(Object.keys(schedule_keywords)[0]);
        }
        setShowKeyword(!showKeyword);
    };

    const closePopup = () => {
        setVisible(false);
        handleClose();
    };

    // Close popup if enter key pressed
    const handleEnterKey = (e) => {
        if (e.key === "Enter") {
            closePopup();
        }
    };

    // Add invalid highlight if timestamp is empty and highlightInvalid is true
    const invalid =  highlightInvalid && !timestamp;

    return (
        <div onKeyDown={handleEnterKey}>
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
                onClose={closePopup}
            >
                {showKeyword ? (
                    <div>
                        <Form.Label>Keyword</Form.Label>
                        <Dropdown
                            value={timestamp}
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
                            value={timestamp}
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
                        checked={showKeyword}
                        onChange={(e) => toggleKeyword(e.target.checked)}
                    />
                </div>
            </PopupDiv>
        </div>
    );
};

TimeField.propTypes = {
    timestamp: PropTypes.string.isRequired,
    setTimestamp: PropTypes.func.isRequired,
    schedule_keywords: PropTypes.object.isRequired,
    highlightInvalid: PropTypes.bool,
    handleClose: PropTypes.func
};
