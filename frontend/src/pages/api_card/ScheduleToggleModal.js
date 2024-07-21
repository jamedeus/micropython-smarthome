import React, { useContext, useState } from 'react';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import InputGroup from 'react-bootstrap/InputGroup';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';
import { ApiCardContext } from 'root/ApiCardContext';
import { numbersOnly } from 'util/validation';

export let showScheduleToggle;

const ScheduleToggleModal = () => {
    // Get function to send API call to node
    const { send_command } = useContext(ApiCardContext);

    // Create states for visibility, target instance, fields
    const [visible, setVisible] = useState(false);
    const [action, setAction] = useState('');
    const [delay, setDelay] = useState('15');
    const [units, setUnits] = useState('minutes');
    const [target, setTarget] = useState('');

    // Takes instance ID and current enable state (bool)
    // Opens modal with opposite of current state pre-selected
    showScheduleToggle = (id, enabled) => {
        setTarget(id);
        setAction(enabled ? 'disable_in' : 'enable_in');
        setVisible(true);
    };

    // Format delay field as user types (prevent non-numeric, limit length)
    const formatDelayField = (newDelay) => {
        // Limit delay to (very) roughly 1 day
        switch(units) {
            case 'seconds':
                return numbersOnly(newDelay).substring(0,5);
            case 'minutes':
                return numbersOnly(newDelay).substring(0,4);
            case 'hours':
                return numbersOnly(newDelay).substring(0,2);
        }
    };

    // Close modal, make API call to node with selection
    const submit = async () => {
        setVisible(false);
        const payload = {
            command: action,
            instance: target,
            delay: delay
        };

        // Convert delay to minutes
        if (units === 'seconds') {
            payload.delay = String(parseInt(payload.delay) / 60);
        } else if (units === 'hours') {
            payload.delay = String(parseInt(payload.delay) * 60);
        }

        const response = await send_command(payload);
        const data = await response.json();
        console.log(data);
    };

    return (
        <Modal show={visible} onHide={() => setVisible(false)} centered>
            <HeaderWithCloseButton
                title="Schedule Toggle"
                onClose={() => setVisible(false)}
                size="3"
            />

            <Modal.Body className="text-center pb-0">
                <p>Enable or disable after a delay.</p>
                <p>Replaces existing timer if present.</p>

                <InputGroup className="mb-3 py-2">
                    <Form.Select
                        defaultValue={action}
                        onChange={(e) => setAction(e.target.value)}
                        className="text-center"
                    >
                        <option value="enable_in">Enable</option>
                        <option value="disable_in">Disable</option>
                    </Form.Select>
                    <InputGroup.Text>in</InputGroup.Text>
                    <Form.Control
                        value={delay}
                        onChange={(e) => setDelay(
                            formatDelayField(e.target.value)
                        )}
                        className="text-center"
                    />
                    <Form.Select
                        defaultValue={units}
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
                    disabled={delay.length === 0}
                    onClick={submit}
                >
                    Schedule
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default ScheduleToggleModal;
