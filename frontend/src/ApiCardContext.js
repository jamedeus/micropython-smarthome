import React, { useState, createContext, useCallback } from 'react';
import PropTypes from 'prop-types';
import { parse_dom_context, getCookie } from 'util/django_util';
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

    // Create state to control fade in/fade out animation
    // Fades in when true, fades out when false (both persist)
    const [loading, setLoading] = useState(true);

    // Create state to control which cards are highlighted when sensor card
    // "Show targets" dropdown option clicked
    const [highlightCards, setHighlightCards] = useState([]);

    // Handler for "Show targets" option in sensor card dropdown
    function show_targets(id) {
        // Add target device IDs to state that controls glow effect
        const params = get_instance_section(id);
        setHighlightCards(params.targets);
        // Add listener to remove highlight on next click
        setTimeout(() => {
            document.addEventListener("click", () => {
                setHighlightCards([]);
            }, {once : true});
        }, 1);
    }

    // Button callback, fade out and redirect to overview
    function overview() {
        setLoading(false);
        if (recording) {
            window.location.href = `/api/recording/${recording}`;
        } else {
            window.location.href = "/api";
        }
    }

    // Reset loading animation when navigated to with browser back button
    window.onpageshow = function(event) {
        if (event.persisted) {
            setLoading(true);
        }
    };

    // Takes instance ID (device1, sensor2, etc), returns category
    // string (used to look up instance in state object)
    function get_instance_category(id) {
        if (id.startsWith('device')) {
            return 'devices';
        } else if (id.startsWith('sensor')) {
            return 'sensors';
        } else {
            throw new Error('Received invalid instance id:', id);
        }
    }

    // Takes instance ID, returns corresponding state object section
    function get_instance_section(id) {
        const category = get_instance_category(id);
        return status[category][id];
    }

    // Takes instance ID and object with param:newValue pairs
    // Updates all params in state object
    function update_instance(id, params) {
        const category = get_instance_category(id);
        setStatus({
            ...status, [category]: {
                ...status[category], [id]: {
                    ...status[category][id], ...params
                }
            }
        });

    }

    // Takes command params, posts to backend, backend makes API
    // call to esp32 using faster non-http compliant protocol
    async function send_command(value) {
        // Add IP of target node
        value["target"] = targetIP;

        // Send to different endpoint if recording macro
        if (recording) {
            return add_macro_action(value);
        }

        // Send to endpoint that forwards payload to ESP32 if not recording
        const result = await fetch('/send_command', {
            method: 'POST',
            body: JSON.stringify(value),
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
                "X-CSRFToken": getCookie('csrftoken')
            }
        });
        return result;
    }

    async function add_macro_action(value) {
        // Add friendly name for all instances except IR Blaster
        if (value.instance) {
            const instanceStatus = get_instance_section(value.instance);
            value["friendly_name"] = instanceStatus.nickname;
        }

        // Add macro name
        const payload = {
            name: recording,
            action: value
        };

        const result = await fetch('/add_macro_action', {
            method: 'POST',
            body: JSON.stringify(payload),
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
                "X-CSRFToken": getCookie('csrftoken')
            }
        });
        return result;
    }

    async function enable_instance(id, enable) {
        // Build payload from args
        const payload = {'command': '', 'instance': id};
        if (enable === true) {
            payload.command = 'enable';
        } else {
            payload.command = 'disable';
        }

        // Send API call to node
        const result = await send_command(payload);

        // If successful update state (re-render immediately, not after update)
        if (result.ok) {
            update_instance(id, "enabled", enable);
            if (enable) {
                // Ensure current_rule is not string (avoid NaN on slider)
                // May be incorrect until next update for non-slider rules, but
                // no other rule types are displayed on the frontend anyway
                let rule;
                const section = get_instance_section(id);
                if (parseInt(section.current_rule)) {
                    rule = section.current_rule;
                } else if (parseInt(section.scheduled_rule)) {
                    rule = section.scheduled_rule;
                } else {
                    rule = section.default_rule;
                }
                update_instance(id, {enabled: true, current_rule: rule});
            } else {
                update_instance(id, {enabled: false});
            }
        } else {
            console.log("Failed to enable:", id);
            console.log(result);
        }
    }

    async function trigger_sensor(id) {
        // Send API call to node
        const payload = {'command': 'trigger_sensor', 'instance': id};
        const result = await send_command(payload);

        // If successful make same change in state (re-render immediately)
        if (result.ok) {
            update_instance(id, {condition_met: true});
        } else {
            console.log("Failed to trigger:", id);
            console.log(result);
        }
    }

    async function turn_on(id, state) {
        const payload = {'command': '', 'instance': id};
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
            console.log("Failed to set power state:", id);
            console.log(result);
        }
    }

    // Handler for rule sliders and buttons, updates local state immediately, calls
    // debounced function to send API call to node when user stops moving slider
    async function set_rule(id, value) {
        update_instance(id, {current_rule: value});
        debounced_set_rule(id, value);
    }

    // Called by set_rule, sends API call to node once user stops moving slider for
    // 150ms (prevents constant API calls saturating ESP32 bandwidth)
    const debounced_set_rule = useCallback(debounce(async (id, rule) => {
        const payload = {
            'command': 'set_rule',
            'instance': id,
            'rule': rule
        };
        const result = await send_command(payload);
        console.log(result);
    }, 150), []);

    // Called by reset option in dropdown, replaces current_rule with scheduled_rule
    async function reset_rule(id) {
        // Send API call to node
        const result = await send_command({'command': 'reset_rule', 'instance': id});

        // If successful make same change in state (re-render immediately)
        if (result.ok) {
            const instance = get_instance_section(id);
            update_instance(id, {current_rule: instance.scheduled_rule});
        } else {
            console.log("Failed to reset rule:", id);
        }
    }

    async function add_schedule_rule(id, timestamp, rule) {
        const result = await send_command({
            'command': 'add_rule',
            'instance': id,
            'time': timestamp,
            'rule': rule
        });

        // Add new rule to state if successful
        if (result.ok) {
            const instance = get_instance_section(id);
            const rules = { ...instance.schedule };
            rules[timestamp] = rule;
            update_instance(id, {schedule: rules});
            return true;
        } else {
            return false;
        }
    }

    async function delete_schedule_rule(id, timestamp) {
        const result = await send_command({
            'command': 'remove_rule',
            'instance': id,
            'rule': timestamp
        });

        // Add new rule to state if successful
        if (result.ok) {
            const instance = get_instance_section(id);
            const rules = { ...instance.schedule };
            delete rules[timestamp];
            update_instance(id, {schedule: rules});
        }
    }

    async function edit_schedule_rule(id, oldTimestamp, newTimestamp, rule) {
        // Add new rule (overwrite existing if timestamp not changed)
        const result = await send_command({
            'command': 'add_rule',
            'instance': id,
            'time': newTimestamp,
            'rule': rule,
            'overwrite': 'overwrite'
        });

        if (result.ok) {
            const instance = get_instance_section(id);
            const rules = { ...instance.schedule };

            // If timestamp was changed delete old rule
            if (oldTimestamp != newTimestamp) {
                const result = await send_command({
                    'command': 'remove_rule',
                    'instance': id,
                    'rule': oldTimestamp
                });
                if (result.ok) {
                    delete rules[oldTimestamp];
                }
            }

            // Add new rule (overwrites if timestamp not changed), update state
            rules[newTimestamp] = rule;
            update_instance(id, {schedule: rules});
            return true;
        } else {
            return false;
        }
    }

    async function add_ir_macro(name, actions) {
        const result = await fetch('/add_ir_macro', {
            method: 'POST',
            body: JSON.stringify({
                ip: targetIP,
                name: name,
                actions: actions
            }),
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
                "X-CSRFToken": getCookie('csrftoken')
            }
        });
        if (result.ok) {
            setIrMacros({ ...irMacros, [name]: actions});
        }
    }

    return (
        <ApiCardContext.Provider value={{
            status,
            setStatus,
            loading,
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
            reset_rule,
            add_schedule_rule,
            delete_schedule_rule,
            edit_schedule_rule,
            add_ir_macro
        }}>
            {children}
        </ApiCardContext.Provider>
    );
};

ApiCardContextProvider.propTypes = {
    children: PropTypes.node,
};
