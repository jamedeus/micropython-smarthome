import React, { useState, createContext, useCallback } from 'react';
import PropTypes from 'prop-types';
import { parse_dom_context, send_post_request } from 'util/django_util';
import { debounce } from 'util/helper_functions';

export const ApiCardContext = createContext();

export const ApiCardContextProvider = ({ children }) => {
    // Load contexts set by django template
    const [status, setStatus] = useState(() => {
        return parse_dom_context("status");
    });
    const [targetIP] = useState(() => {
        return parse_dom_context("target_ip");
    });
    const [apiTargetOptions, _] = useState(() => {
        return parse_dom_context("api_target_options");
    });
    const [irMacros, setIrMacros] = useState(() => {
        return parse_dom_context("ir_macros");
    });
    const [recording] = useState(() => {
        return parse_dom_context("recording");
    });

    // Create state to control SaveRulesToast visibility
    const [showRulesToast, setShowRulesToast] = useState(false);

    // Create state to control which cards are highlighted when sensor card
    // "Show targets" dropdown option clicked
    const [highlightCards, setHighlightCards] = useState([]);

    // Handler for "Show targets" option in sensor card dropdown
    const show_targets = (id) => {
        // Add target device IDs to state that controls glow effect
        const params = get_instance_section(id);
        setHighlightCards(params.targets);
        // Add listener to remove highlight on next click
        setTimeout(() => {
            document.addEventListener("click", () => {
                setHighlightCards([]);
            }, {once : true});
        }, 1);
    };

    // Button callback, redirect to overview
    const overview = () => {
        if (recording) {
            window.location.href = `/api/recording/${recording}`;
        } else {
            window.location.href = "/api";
        }
    };

    // Takes instance ID (device1, sensor2, etc), returns category
    // string (used to look up instance in state object)
    const get_instance_category = (id) => {
        if (id.startsWith('device')) {
            return 'devices';
        } else if (id.startsWith('sensor')) {
            return 'sensors';
        } else {
            /* istanbul ignore next */
            throw new Error('Received invalid instance id:', id);
        }
    };

    // Takes instance ID, returns corresponding state object section
    const get_instance_section = (id) => {
        const category = get_instance_category(id);
        return status[category][id];
    };

    // Takes instance ID and object with param:newValue pairs
    // Updates all params in state object
    const update_instance = (id, params) => {
        const category = get_instance_category(id);
        setStatus({
            ...status, [category]: {
                ...status[category], [id]: {
                    ...status[category][id], ...params
                }
            }
        });
    };

    // Takes command params, posts to backend, backend makes API
    // call to esp32 using faster non-http compliant protocol
    const send_command = async (value) => {
        // Add IP of target node
        value.target = targetIP;

        // Send to different endpoint if recording macro
        if (recording) {
            return add_macro_action(value);
        }

        const response = await send_post_request('/send_command', value);
        return response;
    };

    const add_macro_action = async (value) => {
        // Add friendly name for all instances except IR Blaster
        if (value.instance) {
            const instanceStatus = get_instance_section(value.instance);
            value.friendly_name = instanceStatus.nickname;
        }

        // Add macro name
        const payload = {
            name: recording,
            action: value
        };

        const response = await send_post_request('/add_macro_action', payload);
        return response;
    };

    const enable_instance = async (id, enable) => {
        // Build payload from args
        const payload = {command: '', instance: id};
        if (enable === true) {
            payload.command = 'enable';
        } else {
            payload.command = 'disable';
        }

        // Send API call to node
        const result = await send_command(payload);

        // If successful update state (re-render immediately, not after update)
        if (result.ok) {
            update_instance(id, { enabled: true });
            if (enable) {
                // Ensure current_rule is not string (avoid NaN on slider)
                // May be incorrect until next update for non-slider rules, but
                // no other rule types are displayed on the frontend anyway
                const section = get_instance_section(id);
                if (isNaN(section.current_rule)) {
                    // Use scheduled rule if not NaN
                    if (!isNaN(section.scheduled_rule)) {
                        update_instance(id, {
                            enabled: true,
                            current_rule: section.scheduled_rule
                        });
                    // Use default_rule as last resort (guaranteed to be number)
                    } else {
                        update_instance(id, {
                            enabled: true,
                            current_rule: section.default_rule
                        });
                    }
                }
            } else {
                update_instance(id, { enabled: false });
            }
        } else {
            const error = await result.json();
            console.log(`Failed to ${enable ? 'enable' : 'disable'} ${id},`, error);
        }
    };

    const trigger_sensor = async (id) => {
        // Send API call to node
        const payload = {command: 'trigger_sensor', instance: id};
        const result = await send_command(payload);

        // If successful make same change in state (re-render immediately)
        if (result.ok) {
            update_instance(id, {condition_met: true});
        } else {
            const error = await result.json();
            console.log(`Failed to trigger ${id},`, error);
        }
    };

    const turn_on = async (id, state) => {
        const payload = {command: '', instance: id};
        if (state) {
            payload.command = 'turn_on';
        } else {
            payload.command = 'turn_off';
        }

        // Send API call to node
        const result = await send_command(payload);

        // If successful make same change in state (re-render immediately)
        if (result.ok) {
            update_instance(id, {turned_on: state});
        } else {
            const error = await result.json();
            console.log(`Failed to set power state for ${id},`, error);
        }
    };

    const set_rule = async (id, rule) => {
        update_instance(id, {current_rule: rule});
        const payload = {
            command: 'set_rule',
            instance: id,
            rule: rule
        };
        const result = await send_command(payload);
        console.log(result);
    };

    // Handler for rule sliders and buttons, updates context state immediately,
    // makes API call after 150ms delay (avoid ESP32 DOS from too many calls)
    const debounced_set_rule = async (id, rule) => {
        update_instance(id, {current_rule: rule});
        debounced_set_rule_callback(id, rule);
    };

    // Resets timer if called again within 150ms
    const debounced_set_rule_callback = useCallback(debounce(async (id, rule) => {
        const payload = {
            command: 'set_rule',
            instance: id,
            rule: rule
        };
        const result = await send_command(payload);
        console.log(result);
    }, 150), []);

    // Called by reset option in dropdown, replaces current_rule with scheduled_rule
    const reset_rule = async (id) => {
        // Send API call to node
        const result = await send_command({command: 'reset_rule', instance: id});

        // If successful make same change in state (re-render immediately)
        if (result.ok) {
            const instance = get_instance_section(id);
            update_instance(id, {current_rule: instance.scheduled_rule});
        } else {
            const error = await result.json();
            console.log(`Failed to reset ${id} rule,`, error);
        }
    };

    const add_schedule_rule = async (id, timestamp, rule) => {
        const result = await send_command({
            command: 'add_rule',
            instance: id,
            time: timestamp,
            rule: rule
        });

        // Add new rule to state if successful
        if (result.ok) {
            const instance = get_instance_section(id);
            const rules = { ...instance.schedule };
            rules[timestamp] = rule;
            update_instance(id, {schedule: rules});
            setShowRulesToast(true);
            return true;
        } else {
            return false;
        }
    };

    const delete_schedule_rule = async (id, timestamp) => {
        const result = await send_command({
            command: 'remove_rule',
            instance: id,
            rule: timestamp
        });

        // Add new rule to state if successful
        if (result.ok) {
            const instance = get_instance_section(id);
            const rules = { ...instance.schedule };
            delete rules[timestamp];
            update_instance(id, {schedule: rules});
            setShowRulesToast(true);
            return true;
        } else {
            return false;
        }
    };

    const edit_schedule_rule = async (id, oldTimestamp, newTimestamp, rule) => {
        // Add new rule (overwrite existing if timestamp not changed)
        const result = await send_command({
            command: 'add_rule',
            instance: id,
            time: newTimestamp,
            rule: rule,
            overwrite: 'overwrite'
        });

        if (result.ok) {
            const instance = get_instance_section(id);
            const rules = { ...instance.schedule };

            // If timestamp was changed delete old rule
            if (oldTimestamp != newTimestamp) {
                const result = await send_command({
                    command: 'remove_rule',
                    instance: id,
                    rule: oldTimestamp
                });
                if (result.ok) {
                    delete rules[oldTimestamp];
                }
            }

            // Add new rule (overwrites if timestamp not changed), update state
            rules[newTimestamp] = rule;
            update_instance(id, {schedule: rules});
            setShowRulesToast(true);
            return true;
        } else {
            return false;
        }
    };

    // Called when user clicks yes on SaveRulesToast
    const sync_schedule_rules = async () => {
        const result = await send_post_request(
            '/sync_schedule_rules',
            {ip: targetIP}
        );
        if (!result.ok) {
            const error = await result.json();
            console.error('Failed to sync schedule rules', error);
        }
    };

    // Takes new macro name and array of action strings
    // Sends API call to create macro, adds to state if successful
    const add_ir_macro = async (name, actions) => {
        const payload = {
            ip: targetIP,
            name: name,
            actions: actions
        };
        const response = await send_post_request('/add_ir_macro', payload);
        if (response.ok) {
            setIrMacros({ ...irMacros, [name]: actions });
        }
    };

    // Takes existing macro name and modified actions
    // Sends API call to overwrite actions, updates state if successful
    const edit_ir_macro = async (name, actions) => {
        const payload = {
            ip: targetIP,
            name: name,
            actions: actions
        };
        const response = await send_post_request('/edit_ir_macro', payload);
        if (response.ok) {
            setIrMacros({ ...irMacros, [name]: actions });
        }
    };

    // Takes name of existing IR macro, sends API call to delete, updates state
    const delete_ir_macro = async (name) => {
        const response = await send_command({
            command: 'ir_delete_macro',
            macro_name: name
        });
        if (response.ok) {
            const update = { ...irMacros };
            delete update[name];
            setIrMacros(update);
        }
    };

    return (
        <ApiCardContext.Provider value={{
            status,
            setStatus,
            showRulesToast,
            setShowRulesToast,
            recording,
            highlightCards,
            show_targets,
            get_instance_section,
            apiTargetOptions,
            irMacros,
            overview,
            send_command,
            enable_instance,
            trigger_sensor,
            turn_on,
            set_rule,
            debounced_set_rule,
            reset_rule,
            add_schedule_rule,
            delete_schedule_rule,
            edit_schedule_rule,
            sync_schedule_rules,
            add_ir_macro,
            edit_ir_macro,
            delete_ir_macro
        }}>
            {children}
        </ApiCardContext.Provider>
    );
};

ApiCardContextProvider.propTypes = {
    children: PropTypes.node,
};
