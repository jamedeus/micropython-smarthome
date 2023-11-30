import React, { useState, createContext } from 'react';
import PropTypes from 'prop-types';
import { get_config_template } from './metadata';

// Takes object and key prefix, returns all keys that begin with prefix
function filterObject(obj, prefix) {
    return Object.entries(obj).reduce((acc, [key, value]) => {
        if (key.startsWith(prefix)) {
            acc[key] = value;
        }
        return acc;
    }, {});
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

export const ConfigContext = createContext();

export const ConfigProvider = ({ children }) => {
    // Load config context set by django template
    const element = document.getElementById("config");

    // Use django context as default config if present, otherwise use template
    let defaultConfig;
    if (element) {
        defaultConfig = JSON.parse(element.textContent);
    } else {
        defaultConfig = {
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

    const [config, setConfig] = useState(defaultConfig);

    const updateConfig = newConfig => {
        setConfig(newConfig);
    };

    const logState = () => {
        console.log(config);
    };

    // Handler for add device and add sensor buttons
    const addInstance = (category) => {
        // Get index of new instance
        const index = Object.keys(filterObject(config, category)).length + 1;

        // Add key to state object with empty config
        // Will be populated with metadata template when user selects type
        setConfig({ ...config, [`${category}${index}`]: {} });
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
        const remPx = parseFloat(getComputedStyle(document.documentElement).fontSize)
        const animation_height = card.clientHeight / remPx + 1.5;
        document.documentElement.style.setProperty('--animation-height', `${animation_height}rem`);

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
        const update = { ...config[id], [param]: value }
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

    return (
        <ConfigContext.Provider value=
            {{
                config,
                updateConfig,
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
}

// Called by deleteInstance, decrements IDs of all subsequent instances to prevent gaps
// Example: If device2 is deleted, device3 becomes device2, device4 becomes device3, etc
function update_ids(target, state) {
    // Get category (device or sensor) and index of removed instance
    const category = target.replace(/[0-9]/g, '');
    const index = target.replace(/[a-zA-Z]/g, '');

    // Get list of all instances in same category
    var instances = filterObject(state, category);

    // If target is device get list of sensors (used to update target IDs)
    if (category === 'device') {
        var sensors = filterObject(state, 'sensor');
        // Remove device from all sensor targets
        for (const sensor in sensors) {
            state[sensor]['targets'] = state[sensor]['targets'].filter(item => item !== target);
        }
    }

    // Iterate all instances in category starting from the removed instance index
    for (let i=parseInt(index); i<Object.entries(instances).length+1; i++) {
        // Removed index now available, decrement next index by 1
        const new_id = `${category}${i}`;
        const old_id = `${category}${i+1}`;
        state[new_id] = JSON.parse(JSON.stringify(state[old_id]));
        delete state[old_id];

        // Decrement device index in sensor targets lists to match above
        if (category === 'device') {
            for (const sensor in sensors) {
                if (state[sensor]['targets'].includes(old_id)) {
                    state[sensor]['targets'] = state[sensor]['targets'].filter(item => item !== old_id);
                    state[sensor]['targets'].push(new_id);
                }
            }
        }
    }

    return state;
}

// Delete instance card animation
// Takes array of card divs, index of card to delete, add instance button
// Fades out card to delete, slides up all cards below + add button
async function delete_animation(cards, index, button) {
    // Fade out card to be deleted
    cards[index].classList.add('fade-out');

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
    cards[index].classList.remove('fade-out');
}

export { filterObject };
