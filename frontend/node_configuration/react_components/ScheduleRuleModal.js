import React, { createContext, useContext, useState } from 'react';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import { ConfigContext } from './ConfigContext';
import { get_instance_metadata } from './metadata';
import { schedule_keywords } from './schedule_keywords';
import Dropdown from './inputs/Dropdown';
import RuleSlider from './inputs/RuleSlider';
import { convert_temperature } from './thermostat_util';


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
        fade_rule: false,
        duration: '',
        show_keyword: false,
        metadata: ''
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
            fade_rule: false,
            show_keyword: !is_timestamp(timestamp),
            metadata: metadata
        };

        // If editing fade rule split into params, set fade_rule flag
        if (String(update.rule).startsWith("fade")) {
            const [_, rule, duration] = String(update.rule).split("/");
            update.fade_rule = true;
            update.duration = duration;
            update.rule = rule;
        }

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
    // Get state object that determines modal contents
    const { modalContent, setModalContent } = useContext(ModalContext);

    // Get curent state for target instance
    const { config } = useContext(ConfigContext);
    const instance = config[modalContent.instance];

    // Takes modalContent param name and value, updates and re-renders
    const set_modal_param = (param, value) => {
        setModalContent({ ...modalContent, [param]: value});
    };

    // Handler for slider move events
    const onSliderMove = (value) => {
        setModalContent({ ...modalContent, ["rule"]: value});
    };

    // Handler for slider + and - buttons
    const onButtonClick = (step, direction, min_rule, max_rule) => {
        if (direction === "up") {
            var new_rule = parseFloat(modalContent.rule) + parseFloat(step);
        } else {
            var new_rule = parseFloat(modalContent.rule) - parseFloat(step);
        };

        // Enforce rule limits
        if (new_rule < parseFloat(min_rule)) {
            new_rule = parseFloat(min_rule);
        } else if (new_rule > parseFloat(max_rule)) {
            new_rule = parseFloat(max_rule);
        };

        setModalContent({ ...modalContent, ["rule"]: new_rule});
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
                        onChange={(e) => set_modal_param("timestamp", e.target.value)}
                    />
                </div>
                <div id="keyword-input" className={modalContent.show_keyword === false ? "d-none" : ""}>
                    <Form.Label>Keyword</Form.Label>
                    <Dropdown
                        value={modalContent.timestamp}
                        options={Object.keys(schedule_keywords)}
                        onChange={(value) => set_modal_param("timestamp", value)}
                    />
                </div>

                <div class="d-flex mt-2">
                    <Form.Check
                        type="switch"
                        id="toggle-time-mode"
                        label="Keyword"
                        checked={modalContent.show_keyword}
                        onChange={(e) => set_modal_param("show_keyword", e.target.checked)}
                    />
                </div>
            </Col>
            <Col md={6} className="text-center">
                <Form.Label>Rule</Form.Label>
                {(() => {
                    // Thermostat: Skip switch and return Float slider with temperatures converted
                    if (modalContent.metadata && modalContent.metadata.config_template.units !== undefined) {
                        const rule_limits = modalContent.metadata.rule_limits;
                        return (
                            <RuleSlider
                                rule_value={modalContent.rule}
                                slider_min={convert_temperature(rule_limits[0], "celsius", instance.units)}
                                slider_max={convert_temperature(rule_limits[1], "celsius", instance.units)}
                                slider_step={0.1}
                                button_step={0.5}
                                display_type={"float"}
                                onButtonClick={onButtonClick}
                                onSliderMove={onSliderMove}
                            />
                        );
                    };

                    // All other types: Add correct input for rule_prompt
                    switch(modalContent.metadata.rule_prompt) {
                        case "standard":
                            return (
                                <Dropdown
                                    value={modalContent.rule}
                                    options={["Enabled", "Disabled"]}
                                    onChange={(value) => set_modal_param("rule", value)}
                                />
                            )
                        case "on_off":
                            return (
                                <Dropdown
                                    value={modalContent.rule}
                                    options={["Enabled", "Disabled", "On", "Off"]}
                                    onChange={(value) => set_modal_param("rule", value)}
                                />
                            )
                        case "float_range":
                            return (
                                <RuleSlider
                                    rule_value={modalContent.rule}
                                    slider_min={modalContent.metadata.rule_limits[0]}
                                    slider_max={modalContent.metadata.rule_limits[1]}
                                    slider_step={0.5}
                                    button_step={0.5}
                                    display_type={"float"}
                                    onButtonClick={onButtonClick}
                                    onSliderMove={onSliderMove}
                                />
                            )
                        case "int_or_fade":
                            return (
                                <>
                                    <RuleSlider
                                        rule_value={parseInt(modalContent.rule)}
                                        slider_min={parseInt(config[modalContent.instance]["min_rule"])}
                                        slider_max={parseInt(config[modalContent.instance]["max_rule"])}
                                        slider_step={1}
                                        button_step={1}
                                        display_type={"int"}
                                        onButtonClick={onButtonClick}
                                        onSliderMove={onSliderMove}
                                    />

                                    {/* Fade duration input */}
                                    <div id="duration-input" className={modalContent.fade_rule ? "text-center" : "d-none"}>
                                        <Form.Label className="mt-2">Duration (seconds)</Form.Label>
                                        <Form.Control
                                            type="text"
                                            value={modalContent.duration}
                                            onChange={(e) => set_modal_param("duration", e.target.value)}
                                        />
                                    </div>

                                    {/* Fade mode */}
                                    <div class="d-flex mt-2">
                                        <Form.Check
                                            type="switch"
                                            id="toggle-rule-mode"
                                            label="Fade"
                                            checked={modalContent.fade_rule}
                                            onChange={(e) => set_modal_param("fade_rule", e.target.checked)}
                                        />
                                    </div>
                                </>
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
