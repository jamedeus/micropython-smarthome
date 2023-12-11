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

    // Get current status object, overwrite state, update cards
    // Called every 5 seconds by effect below
    async function get_new_status() {
        try {
            const response = await fetch(`/get_status/${status.metadata.id}`);
            const data = await response.json();
            setStatus(data);
            console.log("update", data)
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
        value["target"] = status.metadata.ip

        const result = await fetch('/send_command', {
            method: 'POST',
            body: JSON.stringify(value),
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
                "X-CSRFToken": getCookie('csrftoken')
            }
        });

        return result
    };

    async function set_rule(id, category, value) {
        let section = { ...status[category] };
        section[id]["current_rule"] = value;
        setStatus({ ...status, [category]: section })
        // TODO debounced API call, prevent slider spam
    }

    return (
        <ApiCardContext.Provider value={{
            status,
            setStatus,
            send_command,
            set_rule
        }}>
            {children}
        </ApiCardContext.Provider>
    );
};

ApiCardContextProvider.propTypes = {
    children: PropTypes.node,
};
