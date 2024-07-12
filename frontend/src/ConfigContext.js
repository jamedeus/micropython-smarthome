import React, { useState, createContext } from 'react';
import PropTypes from 'prop-types';
import { get_config_template } from 'util/metadata';
import { sleep } from 'util/helper_functions';
import { v4 as uuid } from 'uuid';
import { get_instance_metadata, ir_keys } from 'util/metadata';
import { api_target_options, target_node_ip } from 'util/django_util';


// Takes object and key prefix, returns object with all keys that begin with prefix
function filterObject(obj, prefix) {
    return Object.entries(obj).reduce((acc, [key, value]) => {
        if (key.startsWith(prefix)) {
            acc[key] = value;
        }
        return acc;
    }, {});
}

// Takes object and key prefix, returns array of keys that begin with prefix
function filterObjectKeys(obj, prefix) {
    return Object.keys(filterObject(obj, prefix));
}

export const ConfigContext = createContext();

export const ConfigProvider = ({ children }) => {
    // Load config context set by django template
    const [config, setConfig] = useState(() => {
        // Context element created with json_script django filter
        const element = document.getElementById("config");

        let config;
        // Use context if present, otherwise use blank template
        if (element) {
            config = JSON.parse(element.textContent);
        } else {
            config = {
                metadata: {
                    id: '',
                    floor: '',
                    location: '',
                    schedule_keywords: {}
                },
                wifi: {
                    ssid: '',
                    password: ''
                }
            };
        }

        // Check for api-target with invalid target IP (doesn't match any node)
        // If found, clear ip, default_rule, and schedule rules fields
        const apiTargets = Object.entries(config).filter(([id, params]) => {
            return id.startsWith('device') && params._type === 'api-target';
        });
        apiTargets.forEach(([id, params]) => {
            if (!Object.values(api_target_options.addresses).includes(params.ip)) {
                config[id]['ip'] = '';
                config[id]['default_rule'] = '';
                config[id]['schedule'] = {};
            }
        });

        return config;
    });

    // Create state to control card delete animations
    // Card matching ID fades out, cards in category with higher index slide up
    const [deleteing, setDeleteing] = useState({id: '', category: '', index: ''});

    const updateConfig = newConfig => {
        setConfig(newConfig);
    };

    // Create state for device and sensor UUIDs (used as react key)
    // Pre-populate with id-UUID pairs for existing instances (if editing)
    const [UUIDs, setUUIDs] = useState(
        {
            device: Object.fromEntries(
                filterObjectKeys(config, "device").map((id) => [id, uuid()])
            ),
            sensor: Object.fromEntries(
                filterObjectKeys(config, "sensor").map((id) => [id, uuid()])
            )
        }
    );

    // Takes card index, returns UUID
    const getKey = (id, category) => {
        return UUIDs[category][id];
    };

    // Create state object to control invalid field highlight
    const [highlightInvalid, setHighlightInvalid] = useState(false);

    // Handler for add device and add sensor buttons
    const addInstance = (category) => {
        // Get index of new instance
        const index = Object.keys(filterObject(config, category)).length + 1;

        // Add key to state object with empty config
        // Will be populated with metadata template when user selects type
        // _type = undefined used to detect empty and add invalid highlight
        setConfig({ ...config, [`${category}${index}`]: {'_type': undefined} });

        // Create UUID for new instance
        setUUIDs({ ...UUIDs, [category]: {
            ...UUIDs[category], [`${category}${index}`]: uuid()
        }});
    };

    // Handler for delete button on device and sensor cards
    const deleteInstance = async (id) => {
        // Get height of deleted card + 1.5rem (margin between cards)
        const card = document.getElementById(`${id}-card`);
        const remPx = parseFloat(getComputedStyle(document.documentElement).fontSize);
        const animation_height = card.clientHeight / remPx + 1.5;

        // Set CSS var used in delete animation
        document.documentElement.style.setProperty(
            '--animation-height',
            `${animation_height}rem`
        );

        // Start animation, card being deleted will fade out, all cards below
        // will slide up to fill empty space (uses --animation-height)
        setDeleteing({
            id: id,
            category: id.replace(/[0-9]/g, ''),
            index: parseInt(id.replace(/[a-zA-z]/g, ''))
        });

        // Wait for animation to complete
        await sleep(800);

        // Remove instance from config state, reset animation state
        const newConfig = { ...config };
        delete newConfig[id];
        setConfig(update_ids(id, newConfig));
        setDeleteing({id: '', category: '', index: ''});
    };

    // Handler for type select dropdown in device and sensor cards
    const changeInstanceType = (id, category, event) => {
        const template = get_config_template(category, event.target.value);
        setConfig({ ...config, [id]: template});
    };

    // Handler for all inputs inside device and sensor cards
    // Takes device/sensor ID, param, and value; updates state object
    const handleInputChange = (id, param, value) => {
        const update = { ...config[id], [param]: value };
        setConfig({ ...config, [id]: update});
    };

    // Updates multiple instance params in a single event
    // Takes device/sensor ID, full dict of params; overwrites state object section
    const handleInstanceUpdate = (id, params) => {
        setConfig({ ...config, [id]: params});
    };

    // Handler for sensor target select checkboxes
    const handleSensorTargetSelect = (sensor, target, checked) => {
        // Copy config section
        const update = { ... config[sensor] };
        // Add target if not already present
        if (checked) {
            if (update["targets"].indexOf(target) === -1) {
                update["targets"].push(target);
            }
        // Remove existing target if present
        } else {
            update["targets"] = update["targets"].filter(existing => existing !== target);
        }
        setConfig({ ...config, [sensor]: update });
    };

    // Handler for IR target checkboxes
    const handleIrTargetSelect = (target, checked) => {
        const ir_blaster = { ...config.ir_blaster };
        // Add target if not already present
        if (checked) {
            if (ir_blaster.target.indexOf(target) === -1) {
                ir_blaster.target.push(target);
            }
        // Remove existing target if present
        } else {
            ir_blaster.target = ir_blaster.target.filter(existing => existing !== target);
        }
        setConfig({ ...config, ['ir_blaster']: ir_blaster });
    };

    // Called by deleteInstance, decrements IDs of all subsequent instances to prevent gaps
    // Example: If device2 is deleted, device3 becomes device2, device4 becomes device3, etc
    function update_ids(target, state) {
        // Get category (device or sensor) and index of removed instance
        const category = target.replace(/[0-9]/g, '');
        const index = target.replace(/[a-zA-Z]/g, '');

        // Get list of all instances in same category
        const instances = filterObject(state, category);

        // Get UUIDs of all instances in same category
        const newUUIDs = { ...UUIDs[category] };

        // Get list of all sensors (used to update target IDs)
        const sensors = filterObject(state, 'sensor');

        // If target is device remove from all sensor target lists
        if (category === 'device') {
            for (const sensor in sensors) {
                // Prevent error if sensor type not selected yet (no targets key)
                if (state[sensor]['targets']) {
                    state[sensor]['targets'] = state[sensor]['targets'].filter(
                        item => item !== target
                    );
                }
            }
        }

        // Iterate all instances in category starting from the removed instance index
        for (let i=parseInt(index); i<Object.entries(instances).length+1; i++) {
            // Removed index now available, decrement next index by 1
            const new_id = `${category}${i}`;
            const old_id = `${category}${i+1}`;
            state[new_id] = JSON.parse(JSON.stringify(state[old_id]));
            delete state[old_id];

            // Decrement UUID index to keep associated with correct card
            newUUIDs[new_id] = newUUIDs[old_id];
            delete newUUIDs[old_id];

            // Decrement device index in sensor targets lists to match above
            if (category === 'device') {
                for (const sensor in sensors) {
                    if (state[sensor]['targets'].includes(old_id)) {
                        state[sensor]['targets'] = state[sensor]['targets'].filter(
                            item => item !== old_id
                        );
                        state[sensor]['targets'].push(new_id);
                    }
                }
            }
        }

        // Update UUIDs
        setUUIDs({ ...UUIDs, [category]: {
            ...newUUIDs
        }});

        // Return state (calling function updates)
        return state;
    }

    // Takes ApiTarget target node IP, returns object containing all valid
    // options for target (used to populate ApiTargetRuleModal dropdowns)
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

    // Returns ApiTargetRuleModal options for all devices and sensors in config
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

    return (
        <ConfigContext.Provider value=
            {{
                config,
                updateConfig,
                getKey,
                highlightInvalid,
                setHighlightInvalid,
                addInstance,
                deleteInstance,
                changeInstanceType,
                handleInputChange,
                handleInstanceUpdate,
                handleSensorTargetSelect,
                handleIrTargetSelect,
                getTargetNodeOptions,
                deleteing
            }}
        >
            {children}
        </ConfigContext.Provider>
    );
};

ConfigProvider.propTypes = {
    children: PropTypes.node,
};

export { filterObject };
