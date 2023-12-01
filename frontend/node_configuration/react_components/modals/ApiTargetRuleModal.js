import React, { createContext, useContext, useState } from 'react';
import PropTypes from 'prop-types';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import { ConfigContext } from 'root/ConfigContext';
import { api_target_options } from 'util/django_util';

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
        let update = { ...modalContent };
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
        // Otherwise ensure all inputs are empty
        } else {
            update.instance_on = '';
            update.instance_off = '';
            update.command_on = '';
            update.command_off = '';
            update.command_arg_on = '';
            update.command_arg_off = '';
            update.sub_command_on = '';
            update.sub_command_off = '';
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
};

export const ApiTargetRuleModalContents = () => {
    // Get state object that determines modal contents
    const { modalContent, setModalContent } = useContext(ApiTargetModalContext);

    // Listener for all dropdown inputs
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

    // Takes "instance_on" or "instance_off"
    // Returns instance select dropdown with current instance pre-selected
    const get_instance_dropdown = (param) => {
        return (
            <Form.Select
                value={modalContent[param]}
                className="mb-3 modal-dropdown api-command"
                onChange={(e) => set_modal_param(param, e.target.value)}
            >
                <option value="">Select target instance</option>
                {Object.keys(modalContent.target_node_options).map(option => (
                    <option value={option}>{modalContent.target_node_options[option]["display"]}</option>
                ))}
            </Form.Select>
        );
    };

    // Takes currently-selected instance and either "command_on" or "command_off"
    // Returns dropdown with all valid commands for target instance, current command pre-selected
    const get_command_dropdown = (instance, param) => {
        return (
            <Form.Select
                value={modalContent[param]}
                className="mb-3 modal-dropdown api-command"
                onChange={(e) => set_modal_param(param, e.target.value)}
            >
                <option value="">Select command</option>
                {modalContent.target_node_options[instance]["options"].map(option => (
                    <option value={option}>{option}</option>
                ))}
            </Form.Select>
        );
    };

    // Takes selected IR target and either "sub_command_on" or "sub_command_off"
    // Returns dropdown with all keys for selected target, current key pre-selected
    const get_ir_key_dropdown = (target, param) => {
        return (
            <Form.Select
                value={modalContent[param]}
                className="mb-3 modal-input api-command"
                onChange={(e) => set_modal_param(param, e.target.value)}
            >
                <option value="">Select key</option>
                {modalContent.target_node_options.ir_key.keys[target].map(option => (
                    <option value={option}>{option}</option>
                ))}
            </Form.Select>
        );
    };

    // Takes "command_arg_on" or "command_arg_off"
    // Returns input with current command arg pre-filled
    const get_command_arg_input = (param) => {
        return (
            <Form.Control
                type="text"
                value={modalContent[param]}
                className="mb-3 modal-input api-command"
                onChange={(e) => set_modal_param(param, e.target.value)}
            />
        );
    };

    // Return cascading dropdown for currently-viewed action (on or off)
    switch(modalContent.view_on_rule) {
        case true:
            return (
                <>
                    {/* Always show instance select dropdown */}
                    {get_instance_dropdown("instance_on")}

                    {/* Show command dropdown once instance selected */}
                    {(() => {
                        if (modalContent.instance_on && modalContent.instance_on !== "ignore") {
                            return get_command_dropdown(modalContent.instance_on, "command_on");
                        }
                    })()}

                    {/* Show IR target dropdown if instance is IR Blaster and target is selected */}
                    {(() => {
                        if (modalContent.instance_on === "ir_key" && modalContent.command_on) {
                            return get_ir_key_dropdown(modalContent.command_on, "sub_command_on");
                        }
                    })()}

                    {/* Show arg field if command is set_rule, enable_in, or disable_in */}
                    {(() => {
                        if (["enable_in", "disable_in", "set_rule"].includes(modalContent.command_on)) {
                            return get_command_arg_input("command_arg_on");
                        }
                    })()}
                </>
            );
        case false:
            return (
                <>
                    {/* Always show instance select dropdown */}
                    {get_instance_dropdown("instance_off")}

                    {/* Show command dropdown once instance selected */}
                    {(() => {
                        if (modalContent.instance_off && modalContent.instance_off !== "ignore") {
                            return get_command_dropdown(modalContent.instance_off, "command_off");
                        }
                    })()}

                    {/* Show IR target dropdown if instance is IR Blaster and target is selected */}
                    {(() => {
                        if (modalContent.instance_off === "ir_key" && modalContent.command_off) {
                            return get_ir_key_dropdown(modalContent.command_off, "sub_command_off");
                        }
                    })()}

                    {/* Show arg field if command is set_rule, enable_in, or disable_in */}
                    {(() => {
                        if (["enable_in", "disable_in", "set_rule"].includes(modalContent.command_off)) {
                            return get_command_arg_input("command_arg_off");
                        }
                    })()}
                </>
            );
    }
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
        // Ignore: Add ignore keyword, skip all other params
        // Other endpoints: Command followed by target instance (optional arg for some endpoints)
        if (modalContent.instance_on === 'ir_key') {
            output.on.push(modalContent.instance_on, modalContent.command_on, modalContent.sub_command_on);
        } else if (modalContent.instance_on === 'ignore') {
            output.on.push('ignore');
        } else {
            output.on.push(modalContent.command_on, modalContent.instance_on);
            if (modalContent.command_arg_on !== "") {
                output.on.push(modalContent.command_arg_on);
            }
        }
        // Repeat for off command
        if (modalContent.instance_off === 'ir_key') {
            output.off.push(modalContent.instance_off, modalContent.command_off, modalContent.sub_command_off);
        } else if (modalContent.instance_off === 'ignore') {
            output.on.push('ignore');
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
