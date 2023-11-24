import React, { createContext, useContext, useState } from 'react';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import { ConfigContext } from './ConfigContext';
import { get_instance_metadata } from './metadata';
import {get_schedule_keywords_options} from './schedule_keywords';

// Used to identify HH:MM timestamp
const timestamp_regex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;

// Takes timestamp, returns true for HH:MM format, otherwise false
function is_timestamp(timestamp) {
    if (timestamp_regex.test(timestamp)) {
        return true;
    } else {
        return false;
    };
};


export const ModalContext = createContext();

export const ModalContextProvider = ({ children }) => {
    // Get curent state from context
    const { config } = useContext(ConfigContext);

    // Create state objects for modal visibility, contents
    const [show, setShow] = useState(false);
    const [modalContent, setModalContent] = useState({
        instance: '',
        timestamp: '',
        rule: '',
        show_keyword: false,
        prompt: ''
    });

    const handleShow = (instance, timestamp) => {
        // Get metadata for selected instance type (contains rule prompt)
        const category = instance.replace(/[0-9]/g, '');
        const metadata = get_instance_metadata(category, config[instance]["_type"]);

        // Replace modalContent with params for selected rule
        let update = {
            instance: instance,
            timestamp: timestamp,
            rule: config[instance]["schedule"][timestamp],
            show_keyword: !is_timestamp(timestamp),
            prompt: metadata.rule_prompt
        };

        // Set modal contents, show
        setModalContent(update);
        setShow(true);
    };

    const handleClose = () => {
        setShow(false);
    };

    return (
        <ModalContext.Provider value={{ show, modalContent, setModalContent, handleShow, handleClose }}>
            {children}
        </ModalContext.Provider>
    );
};


export const ScheduleRuleModalContents = () => {
    const { modalContent, setModalContent } = useContext(ModalContext);

    const toggle_timestamp_field = (value) => {
        setModalContent({ ...modalContent, ["show_keyword"]: value});
    };

    const set_timestamp = (value) => {
        setModalContent({ ...modalContent, ["timestamp"]: value});
    }

    const set_rule = (value) => {
        setModalContent({ ...modalContent, ["rule"]: value});
    };

    return (
        <Row>
            <Col md={6} className="text-center">
                <div id="timestamp-input" className={modalContent.show_keyword === true ? "d-none" : ""}>
                    <Form.Label>Time</Form.Label>
                    <Form.Control
                        className="text-center"
                        type="time"
                        value={modalContent.timestamp}
                        onChange={(e) => set_timestamp(e.target.value)}
                    />
                </div>
                <div id="keyword-input" className={modalContent.show_keyword === false ? "d-none" : ""}>
                    <Form.Label>Keyword</Form.Label>
                    <Form.Select value={modalContent.timestamp} onChange={(e) => set_timestamp(e.target.value)}>
                        <option>Select a keyword</option>
                        {get_schedule_keywords_options()}
                    </Form.Select>
                </div>

                <div class="d-flex mt-2">
                    <Form.Check
                        type="switch"
                        id="toggle-time-mode"
                        label="Keyword"
                        checked={modalContent.show_keyword}
                        onChange={(e) => toggle_timestamp_field(e.target.checked)}
                    />
                </div>
            </Col>
            <Col md={6} className="text-center">
                <Form.Label>Rule</Form.Label>
                {(() => {
                    switch(modalContent.prompt) {
                        case "standard":
                            return (
                                <Form.Select value={modalContent.rule} onChange={(e) => set_rule(e.target.value)}>
                                    <option disabled>Select default rule</option>
                                    <option value="enabled">Enabled</option>
                                    <option value="disabled">Disabled</option>
                                </Form.Select>
                            )
                        case "on_off":
                            return (
                                <Form.Select value={modalContent.rule} onChange={(e) => set_rule(e.target.value)}>
                                    <option disabled>Select default rule</option>
                                    <option value="enabled">Enabled</option>
                                    <option value="disabled">Disabled</option>
                                    <option value="on">On</option>
                                    <option value="off">Off</option>
                                </Form.Select>
                            )
                    };
                })()}
            </Col>
        </Row>
    );
};


export const ScheduleRuleModal = (contents) => {
    // Get context and callbacks
    const { show, handleShow, handleClose, modalContent } = useContext(ModalContext);

    return (
        <ModalContextProvider>
            <Modal show={show} onHide={handleClose} centered>
                <Modal.Header className="justify-content-between">
                    <button type="button" class="btn-close" style={{visibility: "hidden"}}></button>
                    <h5 class="modal-title">Schedule Rule</h5>
                    <button type="button" class="btn-close" onClick={() => handleClose()}></button>
                </Modal.Header>

                <Modal.Body>
                    {ScheduleRuleModalContents()}
                </Modal.Body>

                <Modal.Footer className="mx-auto">
                    <div id="rule-buttons">
                        <Button variant="success" className="m-1">Submit</Button>
                        <Button variant="danger" className="m-1">Delete</Button>
                    </div>
                </Modal.Footer>
            </Modal>
        </ModalContextProvider>
    );
};
