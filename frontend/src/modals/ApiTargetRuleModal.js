import React, { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import ToggleButton from 'react-bootstrap/ToggleButton';
import Collapse from 'react-bootstrap/Collapse';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';

export let showApiTargetRuleModal;

// Takes dropdown state, hook to set state, target nodes, and visible page bool
// Renders cascading dropdown with correct fields for current selection
const ApiTargetRuleModalContents = ({
    selectedRule,
    setSelectedRule,
    targetNodeOptions,
    showOnRule
}) => {
    // Listener for all inputs
    // Takes on or off, param name, and value; updates selectedRule state
    const set_modal_param = (rule, param, value) => {
        const update = { ...selectedRule[rule], [param]: value};
        // Reset sub commands when main command changes
        if (param === "instance") {
            update.command = '';
            update.command_arg = '';
            update.sub_command = '';
        } else if (param === "command") {
            update.command_arg = '';
            update.sub_command = '';
        }
        setSelectedRule({ ...selectedRule, [rule]: update});
    };

    // Used for all dropdowns in modal
    // Rule is "on" or "off", param is "instance", "command", or "sub_command"
    // Label is shown on the default option (Select <label>)
    // Options is an array of objects with value and display keys
    const ParamDropdown = ({rule, param, label, options}) => {
        return (
            <Form.Select
                value={selectedRule[rule][param]}
                className="mb-3 modal-dropdown api-command"
                onChange={(e) => set_modal_param(rule, param, e.target.value)}
            >
                <option value="">
                    Select {label}
                </option>
                {options.map(option => (
                    <option key={option.value} value={option.value}>
                        {option.display}
                    </option>
                ))}
            </Form.Select>
        );
    };

    ParamDropdown.propTypes = {
        rule: PropTypes.oneOf(['on', 'off']).isRequired,
        param: PropTypes.oneOf(['instance', 'command', 'sub_command']).isRequired,
        label: PropTypes.string.isRequired,
        options: PropTypes.array.isRequired
    };

    // Renders instance select dropdown
    const InstanceDropdown = ({ rule }) => {
        // Array of objects, value is device/sensor ID, display is friendly name
        const options = Object.entries(targetNodeOptions).map(option => {
            return {value: option[0], display: option[1].display};
        });

        return (
            <ParamDropdown
                rule={rule}
                param={'instance'}
                label={'target instance'}
                options={options}
            />
        );
    };

    InstanceDropdown.propTypes = {
        rule: PropTypes.oneOf(['on', 'off']).isRequired
    };

    // Renders dropdown with all valid commands for target instance
    // Only renders if instance has been selected and is not "ignore"
    const CommandDropdown = ({ rule }) => {
        const selectedInstance = selectedRule[rule].instance;
        if (selectedInstance && selectedInstance !== "ignore") {
            // Array of objects, both keys are command name (enable, disable, etc)
            const options = targetNodeOptions[selectedInstance]['options'].map(option => {
                return {value: option, display: option};
            });

            return (
                <ParamDropdown
                    rule={rule}
                    param={'command'}
                    label={'command'}
                    options={options}
                />
            );
        } else {
            return null;
        }
    };

    CommandDropdown.propTypes = {
        rule: PropTypes.oneOf(['on', 'off']).isRequired
    };

    // Renders dropdown with all keys for selected IR target device
    // Only renders if instance is IR Blaster and target has been selected
    const IrKeyDropdown = ({ rule }) => {
        const selectedInstance = selectedRule[rule].instance;
        const selectedIrTarget = selectedRule[rule].command;
        if (selectedInstance === "ir_key" && selectedIrTarget) {
            // Array of objects, both keys are IR remote key names
            const options = targetNodeOptions.ir_key.keys[selectedIrTarget].map(option => {
                return {value: option, display: option};
            });

            return (
                <ParamDropdown
                    rule={rule}
                    param={'sub_command'}
                    label={'key'}
                    options={options}
                />
            );
        } else {
            return null;
        }
    };

    IrKeyDropdown.propTypes = {
        rule: PropTypes.oneOf(['on', 'off']).isRequired
    };

    // Renders text input used to set command arg
    // Only renders if selected command requires arg
    const CommandArgInput = ({ rule }) => {
        const selectedCommand = selectedRule[rule].command;

        // Workaround to prevent losing focus on each keystroke
        const inputRef = useRef(null);
        useEffect(() => {
            inputRef.current?.focus();
        }, []);

        if (["enable_in", "disable_in", "set_rule"].includes(selectedCommand)) {
            return (
                <Form.Control
                    ref={inputRef}
                    type="text"
                    value={selectedRule[rule].command_arg}
                    className="mb-3 modal-input api-command"
                    onChange={(e) => set_modal_param(rule, 'command_arg', e.target.value)}
                />
            );
        } else {
            return null;
        }
    };

    CommandArgInput.propTypes = {
        rule: PropTypes.oneOf(['on', 'off']).isRequired
    };

    return (
        <div className="mx-auto">
            <InstanceDropdown rule={showOnRule ? 'on' : 'off'} />
            <CommandDropdown rule={showOnRule ? 'on' : 'off'} />
            <IrKeyDropdown rule={showOnRule ? 'on' : 'off'} />
            <CommandArgInput rule={showOnRule ? 'on' : 'off'} />
        </div>
    );
};

ApiTargetRuleModalContents.propTypes = {
    selectedRule: PropTypes.object.isRequired,
    setSelectedRule: PropTypes.func.isRequired,
    targetNodeOptions: PropTypes.object.isRequired,
    showOnRule: PropTypes.bool.isRequired
};

// Help button and collapse with instructions and examples
const ApiTargetRuleInstructions = () => {
    // Collapse states
    const [showHelp, setShowHelp] = useState(false);
    const [showExamples, setShowExamples] = useState(false);

    return (
        <>
            <Button
                variant="secondary"
                size="sm"
                className="mx-auto mb-3"
                onClick={() => setShowHelp(!showHelp)}
            >
                Help
            </Button>

            <Collapse in={showHelp}>
                <div>
                    <p className="text-center">
                        Just like other devices, ApiTargets can be turned on/off by sensors or manually. Instead of effecting a physical device they fire API commands.
                    </p>

                    <p className="text-center">
                        Commands are sent to the target node, which can be changed by closing this popup and selecting an option in the &quot;Target Node&quot; dropdown.
                    </p>

                    <p className="text-center">
                        The dropdowns below contain all available options for the current target node. Select a command to fire when this device is turned on, and another for when it is turned off.
                    </p>

                    <p className="text-center">
                        <Button
                            variant="secondary"
                            size="sm"
                            className="mx-auto mb-3"
                            onClick={() => setShowExamples(!showExamples)}
                        >
                            Examples
                        </Button>
                    </p>

                    <Collapse in={showExamples}>
                        <div>
                            <ul>
                                <li>
                                    Two nodes with motion sensors can work together to cover a large room. Set Sensor1 to target the lights, then set Sensor2 to activate Sensor1 with the <b>trigger_sensor</b> option.
                                </li>
                                <li>
                                    The thermostat can change when a door is open or closed. Set up a door sensor targeting this ApiTarget, then select the thermostat and <b>set_rule</b> command below.
                                </li>
                                <li>
                                    Any sensor can turn a TV or Air Conditioner on/off by triggering an ApiTarget targeting an <b>Ir Blaster</b>.
                                </li>
                            </ul>

                            <p className="text-center">
                                <Button
                                    variant="secondary"
                                    size="sm"
                                    className="mx-auto mb-3"
                                    onClick={() => setShowHelp(!showHelp)}
                                >
                                    Close
                                </Button>
                            </p>
                        </div>
                    </Collapse>
                </div>
            </Collapse>
        </>
    );
};

const ApiTargetRuleModal = () => {
    // Create states for modal visibility, visible page
    const [visible, setVisible] = useState(false);
    const [showOnRule, setShowOnRule] = useState(false);

    // Create state for target node options
    const [targetNodeOptions, setTargetNodeOptions] = useState({});

    // Create state for selected dropdown values
    const [selectedRule, setSelectedRule] = useState({
        on: {
            instance: '',
            command: '',
            command_arg: '',
            sub_command: ''
        },
        off: {
            instance: '',
            command: '',
            command_arg: '',
            sub_command: ''
        }
    });

    // Receives dropdown contents object when modal submitted
    // Set by showApiTargetRuleModal (function passed as handleSubmit arg)
    // TODO there must be a better way to do this
    const [onSubmit, setOnSubmit] = useState(() => () => {});

    // Disable submit button until a valid rule is selected
    const [submitDisabled, setSubmitDisabled] = useState(true);

    // Returns true if selectedRule state contains valid rule
    const ruleIsComplete = () => {
        if (subRuleIsComplete(selectedRule.on) && subRuleIsComplete(selectedRule.off)) {
            return true;
        } else {
            return false;
        }
    };

    // Takes on or off key from selectedRule state
    const subRuleIsComplete = (subRule) => {
        if (subRule.instance === 'ignore') {
            return true;
        } else if (!subRule.instance || !subRule.command) {
            return false;
        } else if (subRule.instance === 'ir_key') {
            if (subRule.command && subRule.sub_command) {
                return true;
            } else {
                return false;
            }
        } else if (['enable_in', 'disable_in', 'set_rule'].includes(subRule.command)) {
            if (subRule.command_arg) {
                return true;
            } else {
                return false;
            }
        } else {
            return true;
        }
    };

    // Update submit button enable state when rule changes
    useEffect(() => {
        setSubmitDisabled(!ruleIsComplete());
    }, [selectedRule]);

    // Takes current rule object (pre-fill dropdowns), dropdown option object
    // returned by getTargetNodeOptions, and callback that receives selection
    showApiTargetRuleModal = (current_rule, target_node_options, handleSubmit) => {
        // Update state to pre-select current rule in dropdowns
        let update = { ...selectedRule };

        // If editing existing rule pre-populate dropdowns
        if (current_rule) {
            // IR command uses different order
            // Ignore action requires instance to be "ignore", rest to be blank
            if (current_rule.on[0] === "ir_key" || current_rule.on[0] === "ignore") {
                [update.on.instance, update.on.command, update.on.sub_command] = current_rule.on;
            } else {
                [update.on.command, update.on.instance, update.on.command_arg] = current_rule.on;
            }
            // Repeat for off rule
            if (current_rule.off[0] === "ir_key" || current_rule.off[0] === "ignore") {
                [update.off.instance, update.off.command, update.off.sub_command] = current_rule.off;
            } else {
                [update.off.command, update.off.instance, update.off.command_arg] = current_rule.off;
            }

        // Otherwise ensure all inputs are empty
        } else {
            update.on = {instance: '', command: '', command_arg: '', sub_command: ''};
            update.off = {instance: '', command: '', command_arg: '', sub_command: ''};
        }

        // Prefill dropdowns with current_rule
        setSelectedRule(update);

        // Save target node options
        setTargetNodeOptions(target_node_options);

        // Save callback that receives dropdown contents object on submit
        setOnSubmit(() => handleSubmit);

        // Show modal, default to on rule page
        setShowOnRule(true);
        setVisible(true);
    };

    const save_rule = () => {
        // Takes "on" or "off", returns array of rule params in correct order
        const parse_rule_params = (rule) => {
            // Get dropdown params for requested rule
            const params = selectedRule[rule];

            // Return array of params in order sent to API:
            // - IR Blaster: ir_key, target, key
            // - Ignore: ignore keyword
            // - Other endpoints: command, target instance, (some endpoints) arg
            if (params.instance === 'ir_key') {
                return [params.instance, params.command, params.sub_command];
            } else if (params.instance === 'ignore') {
                return ['ignore'];
            } else {
                const output = [params.command, params.instance];
                if (params.command_arg) {
                    output.push(params.command_arg);
                }
                return output;
            }
        };

        // Convert selectedRule param objects into arrays of params
        const output = {
            on: parse_rule_params('on'),
            off: parse_rule_params('off')
        };

        // Pass rule object to callback function, close modal
        onSubmit(output);
        setVisible(false);
    };

    return (
        <Modal show={visible} onHide={() => setVisible(false)} centered>
            <HeaderWithCloseButton
                title="API Target Rule"
                onClose={() => setVisible(false)}
            />

            <Modal.Body className="d-flex flex-column mx-auto">
                {/* Help button + collapse with instructions */}
                <ApiTargetRuleInstructions />

                {/* Cascading dropdown inputs */}
                <ApiTargetRuleModalContents
                    selectedRule={selectedRule}
                    setSelectedRule={setSelectedRule}
                    targetNodeOptions={targetNodeOptions}
                    showOnRule={showOnRule}
                />

                <ButtonGroup aria-label="Set On/Off command" className="mx-auto">
                    <ToggleButton
                        id="show-on-rule"
                        type="radio"
                        variant="secondary"
                        name="radio"
                        checked={showOnRule}
                        onChange={() => setShowOnRule(true)}
                    >
                        On Action
                    </ToggleButton>
                    <ToggleButton
                        id="show-off-rule"
                        type="radio"
                        variant="secondary"
                        name="radio"
                        checked={!showOnRule}
                        onChange={() => setShowOnRule(false)}
                    >
                        Off Action
                    </ToggleButton>
                </ButtonGroup>
            </Modal.Body>

            <Modal.Footer className="mx-auto">
                <div id="rule-buttons">
                    <Button
                        variant="success"
                        className="m-1"
                        onClick={save_rule}
                        disabled={submitDisabled}
                    >
                        Submit
                    </Button>
                </div>
            </Modal.Footer>
        </Modal>
    );
};

export default ApiTargetRuleModal;
