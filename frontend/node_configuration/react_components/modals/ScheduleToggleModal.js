import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import InputGroup from 'react-bootstrap/InputGroup';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';
import { ApiCardContext } from 'root/ApiCardContext';


export const ScheduleToggleContext = createContext();

export const ScheduleToggleContextProvider = ({ children }) => {
    const [scheduleToggleContent, setScheduleToggleContent] = useState({
        visible: false,
        action: '',
        delay: '15',
        units: 'minutes',
        target: ''
    });

    // Get function to send API call to node
    const {send_command} = useContext(ApiCardContext);

    const handleClose = () => {
        setScheduleToggleContent({ ...scheduleToggleContent, ["visible"]: false });
    };

    // Takes instance ID and current enable state (bool)
    // Opens modal with opposite of current state pre-selected
    const showScheduleToggle = (id, enabled) => {
        const update = {
            ...scheduleToggleContent,
            ["visible"]: true,
            ["target"]: id
        };

        // Set default to opposite of current state
        if (enabled === true) {
            update.action = "disable_in";
        } else {
            update.action = "enable_in";
        }

        setScheduleToggleContent(update);
    };

    const setAction = (action) => {
        setScheduleToggleContent({
            ...scheduleToggleContent,
            ["action"]: action
        });
    };

    const setDelay = (delay) => {
        setScheduleToggleContent({
            ...scheduleToggleContent,
            ["delay"]: formatDelayField(delay, scheduleToggleContent.delay)
        });
    };

    // Format delay field as user types (prevent non-numeric, limit length)
    const formatDelayField = (newDelay, oldDelay) => {
        // Backspace and delete bypass formatting
        if (newDelay.length < oldDelay.length) {
            return newDelay;
        }

        // Remove non-numeric characters
        newDelay = newDelay.replace(/[^\d.]/g, '');

        // Limit delay to (very) roughly 1 day
        if (scheduleToggleContent.units === 'seconds') {
            newDelay = newDelay.substring(0,5);
        } else if (scheduleToggleContent.units === 'minutes') {
            newDelay = newDelay.substring(0,4);
        } else if (scheduleToggleContent.units === 'hours') {
            newDelay = newDelay.substring(0,2);
        }

        return newDelay;
    };

    const setUnits = (units) => {
        setScheduleToggleContent({
            ...scheduleToggleContent,
            ["units"]: units
        });
    };

    const submit = async () => {
        handleClose();
        let payload = {
            'command': scheduleToggleContent.action,
            'instance': scheduleToggleContent.target,
            'delay': scheduleToggleContent.delay
        };

        // Convert delay to minutes
        if (scheduleToggleContent.units === 'seconds') {
            payload.delay = String(parseInt(payload.delay) / 60);
        } else if (scheduleToggleContent.units === 'hours') {
            payload.delay = String(parseInt(payload.delay) * 60);
        }

        const result = await send_command(payload);
        const response = await result.json();
        console.log(response);
    };

    return (
        <ScheduleToggleContext.Provider value={{
            scheduleToggleContent,
            setScheduleToggleContent,
            handleClose,
            showScheduleToggle,
            setAction,
            setDelay,
            setUnits,
            submit
        }}>
            {children}
        </ScheduleToggleContext.Provider>
    );
};

ScheduleToggleContextProvider.propTypes = {
    children: PropTypes.node,
};


export const ScheduleToggleModal = () => {
    // Get function used to make API call
    const {
        scheduleToggleContent,
        handleClose,
        setAction,
        setDelay,
        setUnits,
        submit
    } = useContext(ScheduleToggleContext);

    return (
        <Modal show={scheduleToggleContent.visible} onHide={handleClose} centered>
            <HeaderWithCloseButton
                title="Schedule Toggle"
                onClose={handleClose}
                size="3"
            />

            <Modal.Body className="text-center pb-0">
                <p>Enable or disable after a delay.</p>
                <p>Replaces existing timer if present.</p>

                <InputGroup className="mb-3 py-2">
                    <Form.Select
                        defaultValue={scheduleToggleContent.action}
                        onChange={(e) => setAction(e.target.value)}
                        className="text-center"
                    >
                        <option value="enable_in">Enable</option>
                        <option value="disable_in">Disable</option>
                    </Form.Select>
                    <InputGroup.Text>in</InputGroup.Text>
                    <Form.Control
                        value={scheduleToggleContent.delay}
                        onChange={(e) => setDelay(e.target.value)}
                        className="text-center"
                    />
                    <Form.Select
                        defaultValue={scheduleToggleContent.units}
                        onChange={(e) => setUnits(e.target.value)}
                        className="text-center"
                    >
                        <option value="seconds">Seconds</option>
                        <option value="minutes">Minutes</option>
                        <option value="hours">Hours</option>
                    </Form.Select>
                </InputGroup>
            </Modal.Body>
            <Modal.Footer className="mx-auto pt-0">
                <Button
                    variant="success"
                    disabled={scheduleToggleContent.delay.length === 0}
                    onClick={submit}
                >
                    Schedule
                </Button>
            </Modal.Footer>
        </Modal>
    );
};
