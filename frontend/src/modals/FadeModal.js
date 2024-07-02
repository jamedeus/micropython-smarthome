import React, { useContext, useState } from 'react';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import { ApiCardContext } from 'root/ApiCardContext';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';
import { numbersOnly } from 'util/validation';

export let showFadeModal;

export const FadeModal = () => {
    // Get function to send API call to node
    const { send_command } = useContext(ApiCardContext);

    // Create states for visibility, target instance, fields
    const [visible, setVisible] = useState(false);
    const [target, setTarget] = useState('');
    const [brightness, setBrightness] = useState('');
    const [duration, setDuration] = useState('');

    showFadeModal = (id) => {
        setTarget(id);
        setVisible(true);
    };

    // Close modal, send command to start fade
    const submit = async () => {
        setVisible(false);
        const result = await send_command({
            command: 'set_rule',
            instance: target,
            rule: `fade/${brightness}/${duration}`
        });
        const response = await result.json();
        console.log(response);
    };

    // Submit modal if enter key pressed and both fields have value
    const handleEnterKey = (e) => {
        if (e.key === "Enter" && brightness && duration) {
            submit();
        }
    };

    return (
        <Modal show={visible} onHide={() => setVisible(false)} centered>
            <HeaderWithCloseButton
                title="Start Fade"
                onClose={() => setVisible(false)}
                size="5"
            />

            <Modal.Body className="d-flex">
                <Col className="text-center mx-1">
                    <Form.Label>
                        Target Brightness
                    </Form.Label>
                    <Form.Control
                        type="text"
                        value={brightness}
                        onChange={(e) => setBrightness(
                            numbersOnly(e.target.value)
                        )}
                        onKeyDown={handleEnterKey}
                    />
                </Col>
                <Col className="text-center mx-1">
                    <Form.Label>
                        Duration (seconds)
                    </Form.Label>
                    <Form.Control
                        type="text"
                        value={duration}
                        onChange={(e) => setDuration(
                            numbersOnly(e.target.value).substring(0,5)
                        )}
                        onKeyDown={handleEnterKey}
                    />
                </Col>
            </Modal.Body>
            <Modal.Footer className="mx-auto pt-0">
                <Button
                    variant="success"
                    disabled={!(brightness && duration)}
                    onClick={submit}
                >
                    Start
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default FadeModal;
