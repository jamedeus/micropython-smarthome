import React, { useState, createContext } from 'react';
import PropTypes from 'prop-types';
import { get_config_template } from 'util/metadata';
import { sleep } from 'util/helper_functions';
import { v4 as uuid } from 'uuid';
import { api_target_options } from 'util/django_util';


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

    const updateConfig = newConfig => {
        setConfig(newConfig);
    };

    // Create state for device and sensor UUIDs (used as react key)
    // Pre-populate with id-UUID pairs for existing instances (if editing)
    const [UUIDs, setUUIDs] = useState(
        {
            devices: Object.fromEntries(
                filterObjectKeys(config, "device").map((id) => [id, uuid()])
            ),
            sensors: Object.fromEntries(
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

    const logState = () => {
        console.log(config);
    };

    // Handler for add device and add sensor buttons
    const addInstance = (category) => {
        // Get index of new instance
        const index = Object.keys(filterObject(config, category)).length + 1;

        // Add key to state object with empty config
        // Will be populated with metadata template when user selects type
        // _type = undefined used to detect empty and add invalid highlight
        setConfig({ ...config, [`${category}${index}`]: {'_type': undefined} });

        // Create UUID for new instance
        setUUIDs({ ...UUIDs, [`${category}s`]: {
            ...UUIDs[`${category}s`], [`${category}${index}`]: uuid()
        }});
    };

    // Handler for delete button on device and sensor cards
    const startDeletingInstance = async (id) => {
        // Get category (device or sensor) and index of deleted card
        const category = id.replace(/[0-9]/g, '');
        const index = id.replace(/[a-zA-z]/g, '');

        // Get reference to deleted card, array of cards in category, and category add button
        const card = document.getElementById(`${id}-card`);
        const cards = Array.from(document.getElementById(`${category}s`).children);
        const button = document.getElementById(`add_${category}`);

        // Get animation height (card height + 1.5rem spacing), set CSS var used in animation
        const remPx = parseFloat(getComputedStyle(document.documentElement).fontSize);
        const animation_height = card.clientHeight / remPx + 1.5;
        document.documentElement.style.setProperty(
            '--animation-height',
            `${animation_height}rem`
        );

        // Wait for animation to complete before removing from state object
        await delete_animation(cards, index, button);
        deleteInstance(id);
    };

    // Called from delete button handler after animation completes
    const deleteInstance = (id) => {
        const newConfig = { ...config };
        delete newConfig[id];
        setConfig(update_ids(id, newConfig));
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

    const handleSliderButton = (id, step, direction, min_rule, max_rule) => {
        const update = { ...config[id] };
        if (direction === "up") {
            update.default_rule = parseFloat(update.default_rule) + parseFloat(step);
        } else {
            update.default_rule = parseFloat(update.default_rule) - parseFloat(step);
        }

        // Enforce rule limits
        if (parseFloat(update.default_rule) < parseFloat(min_rule)) {
            update.default_rule = parseFloat(min_rule);
        } else if (parseFloat(update.default_rule) > parseFloat(max_rule)) {
            update.default_rule = parseFloat(max_rule);
        }
        setConfig({ ...config, [id]: update });
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
        const newUUIDs = { ...UUIDs[`${category}s`] };

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
        setUUIDs({ ...UUIDs, [`${category}s`]: {
            ...newUUIDs
        }});

        // Return state (calling function updates)
        return state;
    }

    return (
        <ConfigContext.Provider value=
            {{
                config,
                updateConfig,
                getKey,
                highlightInvalid,
                setHighlightInvalid,
                logState,
                addInstance,
                startDeletingInstance,
                changeInstanceType,
                handleInputChange,
                handleInstanceUpdate,
                handleSensorTargetSelect,
                handleSliderButton,
                handleIrTargetSelect
            }}
        >
            {children}
        </ConfigContext.Provider>
    );
};

ConfigProvider.propTypes = {
    children: PropTypes.node,
};

// Delete instance card animation
// Takes array of card divs, index of card to delete, add instance button
// Fades out card to delete, slides up all cards below + add button
async function delete_animation(cards, index, button) {
    // Fade out card to be deleted
    cards[index].classList.add('fade-out-card');

    // Slide up all cards below, wait for animation to complete
    for (let i=parseInt(index)+1; i<cards.length; i++) {
        cards[i].children[0].classList.add('slide-up');
    }
    button.classList.add('slide-up');
    await sleep(800);

    // Prevent cards jumping higher when hidden card is actually deleted
    for (let i=parseInt(index)+1; i<cards.length; i++) {
        cards[i].children[0].classList.remove('slide-up');
    }
    button.classList.remove('slide-up');
    // Prevent incorrect card being hidden after react re-render
    cards[index].classList.remove('fade-out-card');
}

export { filterObject };
