import React, { useState, createContext, useEffect } from 'react';
import PropTypes from 'prop-types';
import { getCookie } from 'util/django_util';


export const ApiCardContext = createContext();

export const ApiCardContextProvider = ({ children }) => {
    // Load context set by django template
    const [status, setStatus] = useState(() => {
        function parse_dom_context(name) {
            const element = document.getElementById(name);
            if (element) {
                return JSON.parse(element.textContent);
            } else {
                return "";
            }
        }

        // Parse context element created by django template
        return parse_dom_context("context");
    });

    // Create local state for IP address (not included in
    // status updates, will disappear if allowed to update)
    const [targetIP] = useState(status.metadata.ip);

    // Get current status object, overwrite state, update cards
    // Called every 5 seconds by effect below
    async function get_new_status() {
        try {
            const response = await fetch(`/get_status/${status.metadata.id}`);
            const data = await response.json();
            setStatus(data);
            console.log("update", data);
        } catch (error) {
            console.error('Failed to update status:', error);
        }
    }

    // Update state every 5 seconds
    useEffect(() => {
        const timer = setInterval(get_new_status, 5000);
        return () => clearInterval(timer);
    }, []);

    // Takes command params, posts to backend, backend makes API
    // call to esp32 using faster non-http compliant protocol
    async function send_command(value) {
        // Add IP of target node
        value["target"] = targetIP;

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

    async function enable_instance(id, category, enable) {
        // Build payload from args
        const payload = {'command': '', 'instance': id, 'delay_input': ''};
        if (enable === true) {
            payload.command = 'enable';
        } else {
            payload.command = 'disable';
        }

        // Send API call, update state if successful
        const result = await send_command(payload);
        if (result.ok) {
            let section = { ...status[category] };
            section[id]["enabled"] = enable;
            setStatus({ ...status, [category]: section });
        } else {
            console.log("Failed to enable:", id);
            console.log(result);
        }
    }

    async function trigger_sensor(id) {
        const payload = {'command': 'trigger_sensor', 'instance': id};
        const result = await send_command(payload);
        if (result.ok) {
            let section = { ...status["sensors"] };
            section[id]["condition_met"] = true;
            setStatus({ ...status, ["sensors"]: section });
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
        const result = await send_command(payload);
        if (result.ok) {
            let section = { ...status["devices"] };
            section[id]["turned_on"] = state;
            setStatus({ ...status, ["devices"]: section });
        } else {
            console.log("Failed to set power state:", id);
            console.log(result);
        }
    }

    async function set_rule(id, category, value) {
        let section = { ...status[category] };
        section[id]["current_rule"] = value;
        setStatus({ ...status, [category]: section });
        // TODO debounced API call, prevent slider spam
    }

    return (
        <ApiCardContext.Provider value={{
            status,
            setStatus,
            send_command,
            enable_instance,
            trigger_sensor,
            turn_on,
            set_rule
        }}>
            {children}
        </ApiCardContext.Provider>
    );
};

ApiCardContextProvider.propTypes = {
    children: PropTypes.node,
};
