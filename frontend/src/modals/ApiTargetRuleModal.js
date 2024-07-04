import React, { useContext, useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import Form from 'react-bootstrap/Form';
import { ConfigContext, filterObject } from 'root/ConfigContext';
import { HeaderWithCloseButton } from 'modals/HeaderComponents';
import { get_instance_metadata, ir_keys } from 'util/metadata';
import { api_target_options, target_node_ip } from 'util/django_util';

export let showApiTargetRuleModal;

// Takes modal state object and hook to set state
// Renders cascading dropdown with correct fields for current selection
const ApiTargetRuleModalContents = ({ modalContent, setModalContent }) => {
    // Listener for all inputs
    // Takes on or off, param name, and value; updates modalContent state
    const set_modal_param = (rule, param, value) => {
        const update = { ...modalContent[rule], [param]: value};
        // Reset sub commands when main command changes
        if (param === "instance") {
            update.command = '';
            update.command_arg = '';
            update.sub_command = '';
        } else if (param === "command") {
            update.command_arg = '';
            update.sub_command = '';
        }
        setModalContent({ ...modalContent, [rule]: update});
    };

    // Used for all dropdowns in modal
    // Rule is "on" or "off", param is "instance", "command", or "sub_command"
    // Label is shown on the default option (Select <label>)
    // Options is an array of objects with value and display keys
    const ParamDropdown = ({rule, param, label, options}) => {
        return (
            <Form.Select
                value={modalContent[rule][param]}
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
        rule: PropTypes.oneOf(['on', 'off']),
        param: PropTypes.oneOf(['instance', 'command', 'sub_command']).isRequired,
        label: PropTypes.string.isRequired,
        options: PropTypes.array.isRequired
    };

    // Renders instance select dropdown
    const InstanceDropdown = ({ rule }) => {
        // Array of objects, value is device/sensor ID, display is friendly name
        const options = Object.entries(modalContent.target_node_options).map(option => {
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
        const selectedInstance = modalContent[rule].instance;
        if (selectedInstance && selectedInstance !== "ignore") {
            // Array of objects, both keys are command name (enable, disable, etc)
            const options = modalContent.target_node_options[selectedInstance]['options'].map(option => {
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
        const selectedInstance = modalContent[rule].instance;
        const selectedIrTarget = modalContent[rule].command;
        if (selectedInstance === "ir_key" && selectedIrTarget) {
            // Array of objects, both keys are IR remote key names
            const options = modalContent.target_node_options.ir_key.keys[selectedIrTarget].map(option => {
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
        const selectedCommand = modalContent[rule].command;

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
                    value={modalContent[rule].command_arg}
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
        <>
            <InstanceDropdown rule={modalContent.view_on_rule ? 'on' : 'off'} />
            <CommandDropdown rule={modalContent.view_on_rule ? 'on' : 'off'} />
            <IrKeyDropdown rule={modalContent.view_on_rule ? 'on' : 'off'} />
            <CommandArgInput rule={modalContent.view_on_rule ? 'on' : 'off'} />
        </>
    );
};

ApiTargetRuleModalContents.propTypes = {
    modalContent: PropTypes.object.isRequired,
    setModalContent: PropTypes.func.isRequired
};

const ApiTargetRuleModal = () => {
    // Get curent state from global context
    const { config } = useContext(ConfigContext);

    // Create state objects for modal visibility, contents
    const [visible, setVisible] = useState(false);
    const [modalContent, setModalContent] = useState({
        instance: '',
        target_node_options: '',
        show_help: false,
        show_examples: false,
        view_on_rule: true,
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

    // Takes IP, returns object from api_target_options context
    const getTargetNodeOptions = (ip) => {
        // Generate options from current state if self-targeting
        if (ip === '127.0.0.1' || ip === target_node_ip) {
            return getSelfTargetOptions();
        }

        // Find target node options in object if not self-targeting
        const friendly_name = Object.keys(api_target_options.addresses).find(key =>
            api_target_options.addresses[key] === ip
        );
        // Throw error if not found (prevent crash when opening modal)
        if (!friendly_name) {
            throw new Error(
                'getTargetNodeOptions received an IP that does not match an existing node'
            );
        }

        return api_target_options[friendly_name];
    };

    // Builds ApiTarget options for all currently configured devices and sensors
    const getSelfTargetOptions = () => {
        const options = {};

        // Supported by all devices and sensors
        const universalOptions = [
            'enable',
            'disable',
            'enable_in',
            'disable_in',
            'set_rule',
            'reset_rule'
        ];

        // Add options for each configured device and sensor
        const devices = filterObject(config, "device");
        Object.entries(devices).forEach(([device, params]) => {
            // Add display string and universal options
            options[device] = {
                display: `${params.nickname} (${params._type})`,
                options: [ ...universalOptions ]
            };

            // Add on/off for all types except ApiTarget (prevent infinite loop)
            if (params._type !== 'api-target') {
                options[device]['options'].push('turn_on', 'turn_off');
            }
        });
        const sensors = filterObject(config, "sensor");
        Object.entries(sensors).forEach(([sensor, params]) => {
            // Add display string and universal options
            options[sensor] = {
                display: `${params.nickname} (${params._type})`,
                options: [ ...universalOptions ]
            };

            // Add trigger_sensor endpoint for triggerable sensors
            const metadata = get_instance_metadata('sensor', params._type);
            if (metadata.triggerable) {
                options[sensor]['options'].push('trigger_sensor');
            }
        });

        // If IR Blaster with at least 1 target configured, add options for each target
        if (Object.keys(config).includes("ir_blaster") && config.ir_blaster.target.length) {
            options['ir_key'] = {
                display: "Ir Blaster",
                options: [ ...config.ir_blaster.target ],
                keys: {}
            };
            config.ir_blaster.target.forEach(target => {
                options.ir_key.keys[target] = ir_keys[target];
            });
        }

        return options;
    };

    showApiTargetRuleModal = (instance, rule_key) => {
        // Prevent crash if target IP not set or outdated (eg target node deleted)
        const ip = config[instance]["ip"];
        if (!ip || !Object.values(api_target_options.addresses).includes(ip)) {
            alert("Select target node first");
            return false;
        }

        // Replace modalContent with params for selected rule
        let update = { ...modalContent,
            instance: instance,
            rule_key: rule_key,
            schedule_rule: !(rule_key === "default_rule"),
            target_node_options: getTargetNodeOptions(ip),
            show_help: false,
            show_examples: false,
            view_on_rule: true
        };

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
                [update.on.instance, update.on.command, update.on.sub_command] = rule.on;
            } else {
                [update.on.command, update.on.instance, update.on.command_arg] = rule.on;
            }
            // Repeat for off rule
            if (rule.off[0] === "ir_key") {
                [update.off.instance, update.off.command, update.off.sub_command] = rule.off;
            } else {
                [update.off.command, update.off.instance, update.off.command_arg] = rule.off;
            }

        // Otherwise ensure all inputs are empty
        } else {
            update.on = {instance: '', command: '', command_arg: '', sub_command: ''};
            update.off = {instance: '', command: '', command_arg: '', sub_command: ''};
        }

        // Set modal contents, show modal
        setModalContent(update);
        setVisible(true);
    };

    const handleClose = () => {
        setVisible(false);
    };

    const save_rule = () => {
        // Takes "on" or "off", returns array of rule params in correct order
        const parse_rule_params = (rule) => {
            // Get dropdown params for requested rule
            const params = modalContent[rule];

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

        // Convert modalContent param objects into arrays of params
        const output = {
            'on': parse_rule_params('on'),
            'off': parse_rule_params('off')
        };

        // Add rule to correct state key, close modal
        if (modalContent.schedule_rule) {
            config[modalContent.instance]["schedule"][modalContent.rule_key] = JSON.stringify(output);
        } else {
            config[modalContent.instance][modalContent.rule_key] = JSON.stringify(output);
        }
        handleClose();
    };

    return (
        <Modal show={visible} onHide={handleClose} centered>
            <HeaderWithCloseButton title="API Target Rule" onClose={handleClose} />

            <Modal.Body className="d-flex flex-column mx-auto">
                <Button
                    variant="secondary"
                    size="sm"
                    className="mx-auto mb-3"
                    data-bs-toggle="collapse"
                    data-bs-target="#api-rule-modal-help"
                >
                    Help
                </Button>

                <div className="collapse" id="api-rule-modal-help">
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
                            data-bs-toggle="collapse"
                            data-bs-target="#api-rule-modal-examples"
                        >
                            Examples
                        </Button>
                    </p>

                    <div className="collapse" id="api-rule-modal-examples">
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
                                data-bs-toggle="collapse"
                                data-bs-target="#api-rule-modal-help"
                            >
                                Close
                            </Button>
                        </p>
                    </div>
                </div>

                {/* Cascading dropdown inputs */}
                <ApiTargetRuleModalContents
                    modalContent={modalContent}
                    setModalContent={setModalContent}
                />

                <ButtonGroup aria-label="Set On/Off command">
                    <Button
                        variant={modalContent.view_on_rule ? "dark" : "outline-dark"}
                        className="ms-auto"
                        onClick={() => setModalContent({
                            ...modalContent, view_on_rule: true
                        })}
                    >
                        On Action
                    </Button>
                    <Button
                        variant={modalContent.view_on_rule ? "outline-dark" : "dark"}
                        className="me-auto"
                        onClick={() => setModalContent({
                            ...modalContent, view_on_rule: false
                        })}
                    >
                        Off Action
                    </Button>
                </ButtonGroup>
            </Modal.Body>

            <Modal.Footer className="mx-auto">
                <div id="rule-buttons">
                    <Button variant="success" className="m-1" onClick={save_rule}>
                        Submit
                    </Button>
                </div>
            </Modal.Footer>
        </Modal>
    );
};

export default ApiTargetRuleModal;
