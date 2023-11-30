import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import { ConfigContext } from './ConfigContext';
import { api_target_options } from './django_util';

const ipRegex = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;

// Takes IP, returns object from api_target_options context
function getTargetNodeOptions(ip) {
    const friendly_name = Object.keys(api_target_options.addresses).find(key =>
        api_target_options.addresses[key] === ip
    );
    return api_target_options[friendly_name];
}

export const ApiTargetModalContext = createContext();

export const ApiTargetModalContextProvider = ({ children }) => {
    // Get curent state from global context
    const { config } = useContext(ConfigContext);

    // Create state objects for modal visibility, contents
    const [show, setShow] = useState(false);
    const [modalContent, setModalContent] = useState({
        instance: '',
        target_node_options: '',
        show_help: false,
        show_examples: false,
        view_on_rule: true,
        instance_on: '',
        instance_off: '',
        command_on: '',
        command_off: '',
        command_arg_on: '',
        command_arg_off: '',
        sub_command_on: '',
        sub_command_off: '',
    });

    const handleShow = (instance, rule_key) => {
        // Prevent crash if set rule clicked before selecting target
        if (config[instance]["ip"] !== undefined) {
            if ( ! ipRegex.test(config[instance]["ip"])) {
                // TODO highlight field red instead
                alert("Select target node first");
                return false;
            }
        }

        // Replace modalContent with params for selected rule
        let update = { ...modalContent }
        update.instance = instance;
        update.rule_key = rule_key;
        update.schedule_rule = !(rule_key === "default_rule");
        update.target_node_options = getTargetNodeOptions(config[instance]['ip']);
        update.show_help = false;
        update.show_examples = false;
        update.view_on_rule = true;

        // Parse existing rule from state object if it exists
        let rule = "";
        try {
            if (update.schedule_rule) {
                rule = JSON.parse(config[instance]["schedule"][rule_key]);
            } else {
                rule = JSON.parse(config[instance][rule_key]);
            }
        } catch(e) {}

        // If editing existing rule pre-populate dropdowns
        if (rule) {
            // IR command uses different order
            if (rule.on[0] === "ir_key") {
                [update.instance_on, update.command_on, update.sub_command_on] = rule.on;
            // Other endpoints may/may not have arg
            } else {
                update.command_on = rule.on.shift();
                update.instance_on = rule.on.shift();
                if (rule.on.length) {
                    update.command_arg_on = rule.on.shift();
                }
            }

            // Repeat for off command
            if (rule.off[0] === "ir_key") {
                [update.instance_off, update.command_off, update.sub_command_off] = rule.off;
            } else {
                update.command_off = rule.off.shift();
                update.instance_off = rule.off.shift();
                if (rule.off.length) {
                    update.command_arg_off = rule.off.shift();
                }
            }
        }

        // Set modal contents, show
        setModalContent(update);
        setShow(true);
    };

    const handleClose = () => {
        setShow(false);
    };

    return (
        <ApiTargetModalContext.Provider value={{ show, modalContent, setModalContent, handleShow, handleClose }}>
            {children}
        </ApiTargetModalContext.Provider>
    );
};

ApiTargetModalContextProvider.propTypes = {
    children: PropTypes.node,
}

export const ApiTargetRuleModalContents = () => {
    // Get state object that determines modal contents
    const { modalContent, setModalContent } = useContext(ApiTargetModalContext);

    // Takes modalContent param name and value, updates and re-renders
    const set_modal_param = (param, value) => {
        const update = { ...modalContent, [param]: value};
        // Reset sub commands when main command changes
        if (param === "instance_on") {
            update.command_on = '';
            update.command_arg_on = '';
            update.sub_command_on = '';
        } else if (param === "instance_off") {
            update.command_off = '';
            update.command_arg_off = '';
            update.sub_command_off = '';
        } else if (param === "command_on") {
            update.command_arg_on = '';
            update.sub_command_on = '';
        } else if (param === "command_off") {
            update.command_arg_off = '';
            update.sub_command_off = '';
        }
        setModalContent(update);
    };

    // Copy options for shorter strings
    const options = modalContent.target_node_options;

    // return cascading dropdown, each has ternary expression to hide if previous not populated
    return (
        <>
            <div id="on-action" className={modalContent.view_on_rule ? "" : "d-none"}>
                <Form.Select
                    value={modalContent.instance_on}
                    className="mb-3 modal-dropdown api-command"
                    onChange={(e) => set_modal_param("instance_on", e.target.value)}
                >
                    <option value="">Select target instance</option>
                    {Object.keys(options).map(option => (
                        <option value={option}>{options[option]["display"]}</option>
                    ))}
                </Form.Select>

                <Form.Select
                    value={modalContent.command_on}
                    className={modalContent.instance_on ? "mb-3 modal-dropdown api-command" : "d-none"}
                    onChange={(e) => set_modal_param("command_on", e.target.value)}
                >
                    <option value="">Select command</option>
                    {(() => {
                        if (options[modalContent.instance_on]) {
                            let dropdown_options = [];
                            options[modalContent.instance_on]["options"].map(option => (
                                dropdown_options.push(<option value={option}>{option}</option>)
                            ))
                            return dropdown_options;
                        }
                    })()}
                </Form.Select>

                {/* Only used by IR Blaster */}
                <Form.Select
                    value={modalContent.sub_command_on}
                    className={modalContent.instance_on === "ir_key" ? "mb-3 modal-input api-command" : "d-none"}
                    onChange={(e) => set_modal_param("sub_command_on", e.target.value)}
                >
                    <option value="">Select key</option>
                    {(() => {
                        if (modalContent.instance_on === "ir_key" && Object.keys(options.ir_key.keys).includes(modalContent.command_on)) {
                            let dropdown_options = [];
                            options.ir_key.keys[modalContent.command_on].map(option => (
                                dropdown_options.push(<option value={option}>{option}</option>)
                            ))
                            return dropdown_options;
                        }
                    })()}
                </Form.Select>

                {/* Only used for commands which require argument (set rule, enable_in, disable_in) */}
                <Form.Control
                    type="text"
                    value={modalContent.command_arg_on}
                    className={["enable_in", "disable_in", "set_rule"].includes(modalContent.command_on) ? "mb-3 modal-input api-command" : "d-none"}
                    onChange={(e) => set_modal_param("command_arg_on", e.target.value)}
                />
            </div>

            <div id="off-action" className={modalContent.view_on_rule ? "d-none" : ""}>
                <Form.Select
                    value={modalContent.instance_off}
                    className="mb-3 modal-dropdown api-command"
                    onChange={(e) => set_modal_param("instance_off", e.target.value)}
                >
                    <option value="">Select target instance</option>
                    {Object.keys(options).map(option => (
                        <option value={option}>{options[option]["display"]}</option>
                    ))}
                </Form.Select>

                <Form.Select
                    value={modalContent.command_off}
                    className={modalContent.instance_off ? "mb-3 modal-dropdown api-command" : "d-none"}
                    onChange={(e) => set_modal_param("command_off", e.target.value)}
                >
                    <option value="">Select command</option>
                    {(() => {
                        if (options[modalContent.instance_off]) {
                            let dropdown_options = [];
                            options[modalContent.instance_off]["options"].map(option => (
                                dropdown_options.push(<option value={option}>{option}</option>)
                            ))
                            return dropdown_options;
                        }
                    })()}
                </Form.Select>

                {/* Only used by IR Blaster */}
                <Form.Select
                    value={modalContent.sub_command_off}
                    className={modalContent.instance_off === "ir_key" ? "mb-3 modal-input api-command" : "d-none"}
                    onChange={(e) => set_modal_param("sub_command_off", e.target.value)}
                >
                    <option value="">Select key</option>
                    {(() => {
                        if (modalContent.instance_off === "ir_key" && Object.keys(options.ir_key.keys).includes(modalContent.command_off)) {
                            let dropdown_options = [];
                            options.ir_key.keys[modalContent.command_off].map(option => (
                                dropdown_options.push(<option value={option}>{option}</option>)
                            ))
                            return dropdown_options;
                        }
                    })()}
                </Form.Select>

                {/* Only used for commands which require argument (set rule, enable_in, disable_in) */}
                <Form.Control
                    type="text"
                    value={modalContent.command_arg_off}
                    className={["enable_in", "disable_in", "set_rule"].includes(modalContent.command_off) ? "mb-3 modal-input api-command" : "d-none"}
                    onChange={(e) => set_modal_param("command_arg_off", e.target.value)}
                />
            </div>
        </>
    );
};

export const ApiTargetRuleModal = () => {
    // Get context and callbacks
    const { show, handleClose, modalContent, setModalContent } = useContext(ApiTargetModalContext);

    // Get curent state from global context
    const { config } = useContext(ConfigContext);

    const save_rule = () => {
        let output = {'on': [], 'off': []};

        // Add params in correct order
        // IR Blaster: ir_key followed by target and key
        // Other endpoints: Command followed by target instance (optional arg for some endpoints)
        if (modalContent.instance_on === 'ir_key') {
            output.on.push(modalContent.instance_on, modalContent.command_on, modalContent.sub_command_on);
        } else {
            output.on.push(modalContent.command_on, modalContent.instance_on);
            if (modalContent.command_arg_on !== "") {
                output.on.push(modalContent.command_arg_on);
            }
        }
        // Repeat for off command
        if (modalContent.instance_off === 'ir_key') {
            output.off.push(modalContent.instance_off, modalContent.command_off, modalContent.sub_command_off);
        } else {
            output.off.push(modalContent.command_off, modalContent.instance_off);
            if (modalContent.command_arg_off !== "") {
                output.off.push(modalContent.command_arg_off);
            }
        }

        // Add rule to correct state key, close modal
        if (modalContent.schedule_rule) {
            config[modalContent.instance]["schedule"][modalContent.rule_key] = JSON.stringify(output);
        } else {
            config[modalContent.instance][modalContent.rule_key] = JSON.stringify(output);
        }
        handleClose();
    };

    // Takes modalContent param name and value, updates and re-renders
    const set_modal_param = (param, value) => {
        setModalContent({ ...modalContent, [param]: value});
    };

    return (
        <Modal show={show} onHide={handleClose} centered>
            <Modal.Header className="justify-content-between">
                <button type="button" className="btn-close" style={{visibility: "hidden"}}></button>
                <h5 className="modal-title">Api Target Rule</h5>
                <button type="button" className="btn-close" onClick={() => handleClose()}></button>
            </Modal.Header>

            <Modal.Body className="d-flex flex-column mx-auto">
                <button className="btn btn-sm btn-secondary mx-auto mb-3" type="button" data-bs-toggle="collapse" data-bs-target="#api-rule-modal-help" aria-expanded="false" aria-controls="api-rule-modal-help">
                    Help
                </button>

                <div className="collapse" id="api-rule-modal-help">
                    <p className="text-center">Just like other devices, ApiTargets can be turned on/off by sensors or manually. Instead of effecting a physical device they fire API commands.</p>

                    <p className="text-center">Commands are sent to the target node, which can be changed by closing this popup and selecting an option in the &quot;Target Node&quot; dropdown.</p>

                    <p className="text-center">The dropdowns below contain all available options for the current target node. Select a command to fire when this device is turned on, and another for when it is turned off.</p>

                    <p className="text-center">
                        <button className="btn btn-sm btn-secondary" type="button" data-bs-toggle="collapse" data-bs-target="#api-rule-modal-examples" aria-expanded="false" aria-controls="api-rule-modal-examples">
                            Examples
                        </button>
                    </p>

                    <div className="collapse" id="api-rule-modal-examples">
                        <ul>
                            <li>Two nodes with motion sensors can work together to cover a large room. Set Sensor1 to target the lights, then set Sensor2 to activate Sensor1 with the <b>trigger_sensor</b> option.</li>
                            <li>The thermostat can change when a door is open or closed. Set up a door sensor targeting this ApiTarget, then select the thermostat and <b>set_rule</b> command below.</li>
                            <li>Any sensor can turn a TV or Air Conditioner on/off by triggering an ApiTarget targeting an <b>Ir Blaster</b>.</li>
                        </ul>

                        <p className="text-center">
                            <button className="btn btn-sm btn-secondary mb-3" type="button" data-bs-toggle="collapse" data-bs-target="#api-rule-modal-help" aria-expanded="false" aria-controls="api-rule-modal-help">
                                Close
                            </button>
                        </p>
                    </div>
                </div>
                {ApiTargetRuleModalContents()}
                <ButtonGroup aria-label="Set On/Off command">
                    <Button
                        variant={modalContent.view_on_rule ? "dark" : "outline-dark"}
                        className="ms-auto"
                        onClick={() => set_modal_param("view_on_rule", true)}
                    >
                        On Action
                    </Button>
                    <Button
                        variant={modalContent.view_on_rule ? "outline-dark" : "dark"}
                        className="me-auto"
                        onClick={() => set_modal_param("view_on_rule", false)}
                    >
                        Off Action
                    </Button>
                </ButtonGroup>
            </Modal.Body>

            <Modal.Footer className="mx-auto">
                <div id="rule-buttons">
                    <Button variant="success" className="m-1" onClick={save_rule}>Submit</Button>
                </div>
            </Modal.Footer>
        </Modal>
    );
};
